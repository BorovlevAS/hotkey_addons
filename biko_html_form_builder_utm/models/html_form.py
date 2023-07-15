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
        html_output += '  <label for="utm_medium">UTM medium</label>\n <input type="hidden" name="utm_medium" readonly/><br/>\n'
        html_output += '  <label for="utm_campaign">UTM campaign</label><input type="hidden" name="utm_campaign" readonly/><br/>\n'
        html_output += '  <label for="utm_source">UTM source</label><input type="hidden" name="utm_source" readonly/><br/>\n'
        html_output += '  <input type="submit" value="Send"/>\n'
        html_output += "</form>\n"
        html_output += '<script>var queryForm=function(e){var t=!(!e||!e.reset)&&e.reset,n=window.location.toString().split("?");if(n.length>1){var o=n[1].split("&");for(s in o){var r=o[s].split("=");(t||null===sessionStorage.getItem(r[0]))&&sessionStorage.setItem(r[0],decodeURIComponent(r[1]))}}for(var i=document.querySelectorAll("input[type=hidden], input[type=text]"),s=0;s<i.length;s++){var a=sessionStorage.getItem(i[s].name);a&&(document.getElementsByName(i[s].name)[0].value=a)}};setTimeout(function(){queryForm({reset: true})},1e3);</script>'
        self.output_html = html_output
