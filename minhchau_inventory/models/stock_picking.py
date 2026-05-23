from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_assign(self):
        # 1. Chốt chặn Pop-up kiểm tra Hạn Sử Dụng (HSD) trước
        for move in self.move_ids_without_package:
            for line in move.move_line_ids:
                # Odoo gốc dùng trường expiration_date để lưu ngày hết hạn của Lô
                lot_expiry = line.lot_id.expiration_date if line.lot_id and hasattr(line.lot_id, 'expiration_date') else False
                if lot_expiry and lot_expiry < fields.Datetime.now():
                    raise ValidationError(_("⚠️ CHẶN: Thuốc '%s' thuộc lô '%s' đã hết hạn sử dụng!") % (line.product_id.name, line.lot_id.name))

            # 2. Chốt chặn Pop-up kiểm tra Số lượng tồn kho sau
            if move.forecast_availability < move.product_uom_qty:
                raise ValidationError(_("⚠️ CHẶN: Thuốc '%s' không đủ số lượng tồn kho thực tế!") % move.product_id.name)

        return super(StockPicking, self).action_assign()


class StockMove(models.Model):
    _inherit = 'stock.move'

    # Tạo các trường tùy chỉnh cho Nhà thuốc Minh Châu
    x_minhchau_status = fields.Char(string="Lý do chi tiết", compute="_compute_minhchau_status")
    sale_order_url = fields.Char(string="Đường dẫn SO", compute="_compute_sale_order_url")

    # ĐÃ SỬA: Rút gọn chỉ phụ thuộc vào move_line_ids và các trường số lượng của chính stock.move để tránh lỗi liên kết
    @api.depends('state', 'product_uom_qty', 'forecast_availability', 'move_line_ids')
    def _compute_minhchau_status(self):
        for move in self:
            move.x_minhchau_status = _("Đang kiểm tra...")
            
            # Kiểm tra xem có lô nào đi kèm bị quá hạn không
            has_expired_lot = False
            for line in move.move_line_ids:
                lot_expiry = line.lot_id.expiration_date if line.lot_id and hasattr(line.lot_id, 'expiration_date') else False
                if lot_expiry and lot_expiry < fields.Datetime.now():
                    has_expired_lot = True
                    break
            
            # Gán nhãn trạng thái trực quan bằng tiếng Việt cho Dược sĩ
            if has_expired_lot:
                move.x_minhchau_status = _("❌ LÔ THUỐC QUÁ HẠN")
            elif move.state not in ['assigned', 'done'] and move.forecast_availability < move.product_uom_qty:
                move.x_minhchau_status = _("⚠️ THIẾU SỐ LƯỢNG KHO")
            elif move.state == 'assigned':
                move.x_minhchau_status = _("✅ Sẵn sàng xuất kho")
            elif move.state == 'done':
                move.x_minhchau_status = _("Hoàn thành trừ kho")
            else:
                move.x_minhchau_status = _("Chờ xử lý")

    @api.depends('sale_line_id')
    def _compute_sale_order_url(self):
        for move in self:
            sale_order = move.sale_line_id.order_id
            if sale_order:
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                move.sale_order_url = f"{base_url}/web#id={sale_order.id}&model=sale.order&view_type=form"
            else:
                move.sale_order_url = False