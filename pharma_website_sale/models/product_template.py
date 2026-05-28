# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    pharma_product_type = fields.Selection(
        selection=[
            ('rx', 'Thuốc kê đơn'),
            ('otc', 'Thuốc không kê đơn'),
            ('supplement', 'Thực phẩm chức năng'),
        ],
        string='Phân loại dược phẩm',
        default='otc',
        required=True
    )

    pharma_note = fields.Text(
        string='Lưu ý dược phẩm'
    )

    active_ingredients = fields.Char(
        string='Thành phần hoạt chất'
    )

    contraindicated_pregnancy = fields.Boolean(
        string='Chống chỉ định thai kỳ/cho con bú',
        default=False
    )

    contraindicated_kidney = fields.Boolean(
        string='Chống chỉ định suy gan/thận',
        default=False
    )

    contraindicated_hypertension = fields.Boolean(
        string='Chống chỉ định cao huyết áp',
        default=False
    )