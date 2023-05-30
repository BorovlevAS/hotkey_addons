import uuid
from . import forecast_psql

from odoo import api, fields, models, _, tools
from odoo.exceptions import ValidationError


class ReportForecastWizard(models.TransientModel):
    _name = "biko.report.forecast.wizard"

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.user.company_id.id,
    )

    categories_ids = fields.Many2many("product.category", string="Categories")
    product_ids = fields.Many2many("product.product", string="Products")

    def fill_moves_data(self, unique_id):
        self.env["biko.report.forecast"].sudo().search([("uid", "=", unique_id)]).unlink()
        sql = forecast_psql.SQL_QUERY
        need_and = False
        if self.company_id:
            need_and = True
            sql += " WHERE prod_demands.company_id = " + str(self.company_id.id)

        if self.categories_ids:
            need_and = True
            category_ids = tuple(self.categories_ids.ids)
            sql += (
                " AND pp.categ_id IN " + str(category_ids) if need_and else " WHERE pp.categ_id IN " + str(category_ids)
            )

        if self.product_ids:
            need_and = True
            product_ids = tuple(self.product_ids.ids)
            sql += (
                " AND prod_demands.product_id IN " + str(product_ids)
                if need_and
                else " WHERE prod_demands.product_id IN " + str(product_ids)
            )

        result = self.env.cr.execute(sql)

        data = self.env.cr.dictfetchall()

        for item in data:
            item.update({"uid": unique_id})
            self.env["biko.report.forecast"].sudo().create(item)

    def open_report(self):

        unique_id = uuid.uuid4().hex
        self.fill_moves_data(unique_id)

        action = {
            "name": "Forecast Report (HOTKEY)",
            "type": "ir.actions.act_window",
            "view_mode": "tree",
            "res_model": "biko.report.forecast",
            "view_id": self.env.ref("biko_report_forecast.biko_report_forecast").id,
            "domain": [("uid", "=", unique_id)],
        }

        return action
