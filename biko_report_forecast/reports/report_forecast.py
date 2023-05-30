from odoo import fields, models


class ReportForecast(models.Model):
    _name = "biko.report.forecast"
    _description = "Forecast Report (HOTKEY)"

    uid = fields.Char(readonly=True)
    company_id = fields.Many2one("res.company", string="Company", readonly=True)
    product_id = fields.Many2one("product.product", string="Product", readonly=True)
    default_code = fields.Char(string="Internal Reference", readonly=True)
    category_id = fields.Many2one("product.category", string="Category", readonly=True)
    min_qty = fields.Float("Min Qty", readonly=True)
    min_qty_multiple = fields.Float("Min Qty Multiple", readonly=True)
    uom_id = fields.Many2one("uom.uom", string="UoM", readonly=True)
    qty_demand = fields.Float("Demand Qty", readonly=True)
    qty_done = fields.Float("Done Qty", readonly=True)
    qty_reserved = fields.Float("Reserved Qty", readonly=True)
    qty_rest_demand = fields.Float("Rest Demand Qty", readonly=True)
    rest_quantity = fields.Float("Rest Qty", readonly=True)
    rest_reserved_quantity = fields.Float("Rest Reserved Qty", readonly=True)
