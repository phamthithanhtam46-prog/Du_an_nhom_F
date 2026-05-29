from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    is_rx_prescription = fields.Selection([
        ('no', 'Không'),
        ('yes', 'Có')
    ], string='Đây có phải đơn thuốc kê đơn Rx không?', default='no', required=True)
    
    rx_pharmacist_id = fields.Many2one(
        'res.users', 
        string='Dược sĩ phụ trách', 
        default=lambda self: self.env.user
    )
    is_rx_confirmed = fields.Boolean(string='Tôi xác nhận đơn thuốc Rx này đã đủ điều kiện để bán')
    rx_confirmation_note = fields.Text(string='Ghi chú kiểm tra đơn thuốc')

    def create_invoices(self):
        # Kiểm tra Rule 4: Nếu là Rx nhưng chưa xác nhận
        if self.is_rx_prescription == 'yes' and not self.is_rx_confirmed:
            raise UserError(_("Đơn thuốc Rx chưa được Dược sĩ xác nhận đủ điều kiện bán. Vui lòng kiểm tra và xác nhận trước khi tạo hóa đơn."))

        # Lưu thông tin xác nhận vào Sales Order trước khi tạo hóa đơn (Rule 5)
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        for order in sale_orders:
            order.write({
                'is_rx_prescription': self.is_rx_prescription == 'yes',
                'rx_pharmacist_id': self.rx_pharmacist_id.id if self.is_rx_prescription == 'yes' else False,
                'is_rx_confirmed': self.is_rx_confirmed if self.is_rx_prescription == 'yes' else False,
                'rx_confirmation_note': self.rx_confirmation_note if self.is_rx_prescription == 'yes' else False,
            })
            
        # Gọi luồng chuẩn tạo hóa đơn
        res = super(SaleAdvancePaymentInv, self).create_invoices()
        return res
