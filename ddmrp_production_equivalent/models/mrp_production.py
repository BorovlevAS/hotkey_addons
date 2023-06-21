from odoo import SUPERUSER_ID, _, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def _get_product_search_criteria(self, bom_line):
        return [("categ_id", "child_of", bom_line.product_id.categ_id.id)]

    def _get_product_equivalent(self, bom_line, requested_qty):
        # get all the other products in the same product category
        p_obj = self.env["product.product"]
        products = p_obj.search(
            self._get_product_search_criteria(bom_line),
            order="priority asc, id asc",
        )
        # exclude the non-equivalent parts listed in the BOM line and the
        # current product
        products -= bom_line.nonequivalent_product_ids + bom_line.product_id
        product_eq = False
        for product in products:
            if product.qty_available > requested_qty:
                product_eq = product
                break
        return product_eq

    def _get_move_raw_values(
        self,
        product_id,
        product_uom_qty,
        product_uom,
        operation_id=False,
        bom_line=False,
    ):
        data = super()._get_move_raw_values(
            product_id, product_uom_qty, product_uom, operation_id, bom_line
        )

        if not bom_line.use_equivalences:
            return data
        if bom_line.product_id.qty_available > product_uom_qty:
            return data

        product_equivalent = self._get_product_equivalent(bom_line, product_uom_qty)

        if product_equivalent:
            body = _(
                "{product_name}<br> has been replaced by <br>{product_equ}."
            ).format(
                product_name=product_id.name_get()[0][1],
                product_equ=product_equivalent.name_get()[0][1],
            )
            data.update(
                {
                    "price_unit": product_equivalent.standard_price,
                    "product_id": product_equivalent.id,
                }
            )
            odoobot_id = self.env.user.browse(SUPERUSER_ID).partner_id.id
            if self._origin:
                self._origin.message_post(body=body, author_id=odoobot_id)
            else:
                channel_info = self.env["mail.channel"].channel_get(
                    partners_to=[self.env.user.partner_id.id, odoobot_id]
                )
                channel = self.env["mail.channel"].browse(channel_info["id"])
                channel.message_notify(
                    partner_ids=[
                        self.env.user.partner_id.id,
                    ],
                    body=body,
                    author_id=odoobot_id,
                )

        return data
