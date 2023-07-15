import ast
import base64
import json
import logging
from datetime import datetime

import odoo.http as http
import requests
import werkzeug
from odoo.addons.html_form_builder.controllers.main import (
    HtmlFieldResponse,
    HtmlFormController,
)
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)


class HtmlFormControllerInherit(HtmlFormController):
    def get_tracking_fields(self):
        return [
            # ("URL_PARAMETER", "FIELD_NAME_MIXIN", "NAME_IN_COOKIES")
            ("utm_campaign", "campaign_id", "utm.campaign"),
            ("utm_source", "source_id", "utm.source"),
            ("utm_medium", "medium_id", "utm.medium"),
        ]

    def process_form(self, kwargs):
        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        if values["my_pie"] != "3.14":
            return "You touched my pie!!!"

        # Check if this form still exists
        if (
            http.request.env["html.form"]
            .sudo()
            .search_count([("id", "=", int(values["form_id"]))])
            == 0
        ):
            return "The form no longer exists"

        entity_form = (
            http.request.env["html.form"].sudo().browse(int(values["form_id"]))
        )

        ref_url = ""
        if "Referer" in http.request.httprequest.headers:
            ref_url = http.request.httprequest.headers["Referer"]

        # Captcha Check
        if entity_form.captcha:
            # Redirect them back if they didn't answer the captcha
            if "g-recaptcha-response" not in values:
                return werkzeug.utils.redirect(ref_url)

            payload = {
                "secret": str(entity_form.captcha_secret_key),
                "response": str(values["g-recaptcha-response"]),
            }
            response_json = requests.post(
                "https://www.google.com/recaptcha/api/siteverify", data=payload
            )

            if response_json.json()["success"] is not True:
                return werkzeug.utils.redirect(ref_url)

        secure_values = {}
        history_values = {}
        return_errors = []
        insert_data_dict = []
        form_error = False

        # populate an array which has ONLY the fields that are in the form (prevent injection)
        for fi in entity_form.fields_ids:
            # Required field check
            if fi.setting_general_required and fi.html_name not in values:
                return_item = {
                    "html_name": fi.html_name,
                    "error_messsage": "This field is required",
                }
                return_errors.append(return_item)
                form_error = True

            if fi.html_name in values:
                method = "_process_html_%s" % (fi.field_type.html_type,)
                action = getattr(self, method, None)

                if fi.field_type.html_type == "file_select":
                    # Also insert the filename
                    filename_field = str(fi.field_id.name) + "_filename"
                    secure_values[filename_field] = values[fi.html_name].filename

                if not action:
                    raise NotImplementedError(
                        "Method %r is not implemented on %r object." % (method, self)
                    )

                field_valid = HtmlFieldResponse()

                field_valid = action(fi, values[fi.html_name], values)

                if field_valid.error == "":
                    secure_values[fi.field_id.name] = field_valid.return_data
                    insert_data_dict.append(
                        {
                            "field_id": fi.field_id.id,
                            "insert_value": field_valid.history_data,
                        }
                    )
                else:
                    return_item = {
                        "html_name": fi.html_name,
                        "error_messsage": field_valid.error,
                    }
                    return_errors.append(return_item)
                    form_error = True

        if form_error:
            return json.JSONEncoder().encode(
                {"status": "error", "errors": return_errors}
            )
        else:
            new_history = (
                http.request.env["html.form.history"]
                .sudo()
                .create({"ref_url": ref_url, "html_id": entity_form.id})
            )

            for insert_field in insert_data_dict:
                new_history.insert_data.sudo().create(
                    {
                        "html_id": new_history.id,
                        "field_id": insert_field["field_id"],
                        "insert_value": insert_field["insert_value"],
                    }
                )

            # default values
            for df in entity_form.defaults_values:
                if df.field_id.ttype == "many2many":
                    secure_values[df.field_id.name] = [
                        (
                            4,
                            request.env[df.field_id.relation]
                            .sudo()
                            .search([("name", "=", df.default_value)])[0]
                            .id,
                        )
                    ]
                elif df.field_id.ttype == "many2one":
                    secure_values[df.field_id.name] = int(df.default_value)
                else:
                    if df.default_value == "user_id":
                        secure_values[df.field_id.name] = request.env.user.id
                    elif df.default_value == "partner_id":
                        secure_values[df.field_id.name] = request.env.user.partner_id.id
                    else:
                        secure_values[df.field_id.name] = df.default_value

                new_history.insert_data.sudo().create(
                    {
                        "html_id": new_history.id,
                        "field_id": df.field_id.id,
                        "insert_value": df.default_value,
                    }
                )

            # UTM-labels
            for url_param, field_name, comodel_name in self.get_tracking_fields():
                value = values.get(url_param, False)
                if isinstance(value, str) and value:
                    Model = http.request.env[comodel_name]
                    records = Model.search([("name", "=", value)], limit=1)
                    if not records:
                        if "is_website" in records._fields:
                            records = Model.create({"name": value, "is_website": True})
                        else:
                            records = Model.create({"name": value})
                    value = records.id
                if value:
                    secure_values[field_name] = value

            try:
                new_record = (
                    http.request.env[entity_form.model_id.model]
                    .sudo()
                    .create(secure_values)
                )
            except Exception as e:
                _logger.error(str(e))
                return "Failed to insert record<br/>\n" + str(e)

            new_history.record_id = new_record.id

            # Execute all the server actions
            for sa in entity_form.submit_action:
                method = "_html_action_%s" % (sa.setting_name,)
                action = getattr(self, method, None)

                if not action:
                    raise NotImplementedError(
                        "Method %r is not implemented on %r object." % (method, self)
                    )

                # Call the submit action, passing the action settings and the history object
                action(sa, new_history, values)

            if "is_ajax_post" in values:
                return json.JSONEncoder().encode(
                    {"status": "success", "redirect_url": entity_form.return_url}
                )
            else:
                return werkzeug.utils.redirect(entity_form.return_url)
