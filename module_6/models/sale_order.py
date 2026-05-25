# -*- coding: utf-8 -*-
from odoo import models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        for order in self:
            for line in order.order_line:
                product = line.product_id
                if not product:
                    continue
                if product.product_tmpl_id.pharma_product_type == 'rx':
                    prescription = self.env['pharmacy.prescription'].search([
                        ('sale_order_id', '=', order.id),
                        ('state', '=', 'confirmed')
                    ], limit=1)
                    if not prescription:
                        raise ValidationError(
                            'Sản phẩm "%s" là thuốc kê đơn (Rx). Không được phép bán trực tiếp.\n'
                            'Vui lòng tạo và duyệt đơn thuốc trước.' % product.display_name
                        )
        return super().action_confirm()
