from odoo import _, api, fields, models
from odoo.http import request


class HtmlForm(models.Model):
    _inherit = "html.form"

    def generate_form(self):
        html_output = ""
        html_output += (
            '<form method="POST" action="'
            + request.httprequest.host_url
            + 'form/insert" enctype="multipart/form-data">\n'
        )
        html_output += '  <input style="display:none;" name="my_pie" value="3.14"/>\n'

        html_output += "  <h1>" + self.name + "</h1>\n"

        for fe in self.fields_ids:
            # each field type has it's own function that way we can make plugin modules with new field types
            method = "_generate_html_%s" % (fe.field_type.html_type,)
            action = getattr(self, method, None)

            if not action:
                raise NotImplementedError(
                    "Method %r is not implemented on %r object." % (method, self)
                )

            html_output += action(fe)

        html_output += (
            '  <input type="hidden" name="form_id" value="' + str(self.id) + '"/>\n'
        )
        html_output += '  <div style="display:none;">\n'
        html_output += '    <input type="hidden" name="utm_medium" readonly/><br/>\n'
        html_output += '    <input type="hidden" name="utm_campaign" readonly/><br/>\n'
        html_output += '    <input type="hidden" name="utm_source" readonly/><br/>\n'
        html_output += "  </div>\n"
        html_output += '  <input type="submit" value="Send"/>\n'
        html_output += "</form>\n"
        html_output += '<script>const queryForm=e=>{var t=!(!e||!e.reset)&&e.reset,e=window.location.toString().split("?");if(1<e.length){var n=e[1].split("&");for(s in n){var o=n[s].split("=");!t&&null!==sessionStorage.getItem(o[0])||sessionStorage.setItem(o[0],decodeURIComponent(o[1]))}}for(var r=document.querySelectorAll("input[type=hidden], input[type=text]"),s=0;s<r.length;s++){var a=sessionStorage.getItem(r[s].name);a&&document.getElementsByName(r[s].name).forEach(e=>e.value=a)}};document.addEventListener("DOMContentLoaded",e=>queryForm({reset:!0}));</script>'
        self.output_html = html_output
