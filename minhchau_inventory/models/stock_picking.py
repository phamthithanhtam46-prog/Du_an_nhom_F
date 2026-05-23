# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date


class StockPicking(models.Model):
    """
    Kế thừa model stock.picking (Phiếu Kho) của Odoo.
    Thêm chốt chặn kiểm tra Hạn Sử Dụng (HSD) theo đúng sơ đồ BPMN:
        Tiếp nhận đơn → Kiểm tra HSD → (Hết hạn?) → Kiểm tra tồn kho → ...
    """
    _inherit = 'stock.picking'

    def action_confirm(self):
        """
        Override action_confirm() để chèn bước Kiểm tra HSD vào TRƯỚC
        toàn bộ logic mặc định của Odoo (giữ chỗ, kiểm tra tồn kho...).

        Luồng xử lý theo BPMN:
            [1] Kiểm tra HSD  ← chạy tại đây, TRƯỚC super()
                 ├─ Hết hạn  → raise ValidationError (chặn cứng, dừng toàn bộ)
                 └─ Còn hạn  → tiếp tục
            [2] super().action_confirm() ← Odoo kiểm tra tồn kho + tạo phiếu xuất
        """
        today = date.today()

        for picking in self:
            # Chỉ kiểm tra HSD trên phiếu XUẤT KHO (outgoing)
            # để không ảnh hưởng phiếu nhập kho hay điều chuyển nội bộ
            if picking.picking_type_code != 'outgoing':
                continue

            for move in picking.move_ids:
                product = move.product_id

                # Duyệt qua từng move line để lấy thông tin lô hàng (lot)
                for move_line in move.move_line_ids:
                    lot = move_line.lot_id

                    # Bỏ qua nếu sản phẩm không theo dõi lô hàng
                    if not lot:
                        continue

                    # Lấy ngày hết hạn từ trường expiration_date của lot
                    # (trường này có sẵn khi bật tính năng Lot/Serial Number + Expiration Date)
                    expiration_date = lot.expiration_date

                    # Nếu lô hàng KHÔNG có ngày HSD → bỏ qua, cho phép tiếp tục
                    if not expiration_date:
                        continue

                    # =====================================================
                    # CHỐT CHẶN HSD - Trái tim của nghiệp vụ BPMN
                    # Nếu ngày hết hạn < ngày hôm nay → hết hạn → CHẶN
                    # =====================================================
                    expiration_date_only = expiration_date.date() \
                        if hasattr(expiration_date, 'date') \
                        else expiration_date

                    if expiration_date_only < today:
                        raise ValidationError(_(
                            "⚠️ CẢNH BÁO: THUỐC ĐÃ HẾT HẠN SỬ DỤNG!\n\n"
                            "Sản phẩm : %s\n"
                            "Lô hàng  : %s\n"
                            "Hạn SD   : %s\n"
                            "Hôm nay  : %s\n\n"
                            "Vui lòng liên hệ Dược sĩ để thay đổi sản phẩm "
                            "hoặc chọn lô hàng còn hạn sử dụng."
                        ) % (
                            product.display_name,
                            lot.name,
                            expiration_date_only.strftime('%d/%m/%Y'),
                            today.strftime('%d/%m/%Y'),
                        ))

        # =====================================================================
        # Chỉ đến đây khi TẤT CẢ lô hàng đều CÒN HẠN
        # Gọi super() để Odoo chạy tiếp: Kiểm tra tồn kho → Tạo phiếu xuất kho
        # =====================================================================
        return super(StockPicking, self).action_confirm()