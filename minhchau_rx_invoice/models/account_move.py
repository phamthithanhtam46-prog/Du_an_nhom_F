from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    is_rx_prescription = fields.Boolean(string='Là đơn thuốc Rx', readonly=True, copy=False)
    rx_pharmacist_id = fields.Many2one('res.users', string='Dược sĩ phụ trách', readonly=True, copy=False)
    is_rx_confirmed = fields.Boolean(string='Đã xác nhận đủ điều kiện bán', readonly=True, copy=False)
    rx_confirmation_note = fields.Text(string='Ghi chú kiểm tra', readonly=True, copy=False)
