from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_rx_prescription = fields.Boolean(string='Là đơn thuốc Rx', readonly=True, copy=False)
    rx_pharmacist_id = fields.Many2one('res.users', string='Dược sĩ phụ trách', readonly=True, copy=False)
    is_rx_confirmed = fields.Boolean(string='Đã xác nhận đủ điều kiện bán', readonly=True, copy=False)
    rx_confirmation_note = fields.Text(string='Ghi chú kiểm tra', readonly=True, copy=False)

    def _prepare_invoice(self):
        # Kế thừa để copy thông tin Rx sang Invoice
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals.update({
            'is_rx_prescription': self.is_rx_prescription,
            'rx_pharmacist_id': self.rx_pharmacist_id.id,
            'is_rx_confirmed': self.is_rx_confirmed,
            'rx_confirmation_note': self.rx_confirmation_note,
        })
        return invoice_vals
