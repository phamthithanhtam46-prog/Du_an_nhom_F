from odoo import models, fields
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    prescription_required = fields.Boolean(
        string='Yêu cầu kê đơn'
    )