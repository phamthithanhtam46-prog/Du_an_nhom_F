# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date


class StockPicking(models.Model):
    """
    Kế thừa model stock.picking (Phiếu Kho) của Odoo.
    Chốt chặn theo đúng sơ đồ BPMN Nhà thuốc Minh Châu:
        Tiếp nhận đơn
            → [1] Kiểm tra HSD      → Hết hạn?   → CHẶN (lỗi HSD)
            → [2] Kiểm tra tồn kho  → Không đủ?  → CHẶN (lỗi tồn kho)
            → [3] Tạo phiếu xuất kho + trừ kho
    """
    _inherit = 'stock.picking'

    def action_validate(self):
        """
        Override action_validate() — chạy khi Dược sĩ bấm nút VALIDATE.

        Luồng xử lý theo BPMN:
            [1] Kiểm tra HSD trước  ← CHỐT CHẶN 1
                 ├─ Hết hạn  → ValidationError (chặn cứng)
                 └─ Còn hạn  → tiếp tục

            [2] Kiểm tra tồn kho    ← CHỐT CHẶN 2
                 ├─ Không đủ SL → ValidationError (nhắc quay lại Sale Order)
                 └─ Đủ SL       → tiếp tục

            [3] super().action_validate() ← Odoo tạo phiếu xuất + trừ kho
        """
        today = date.today()

        for picking in self:
            # Chỉ kiểm tra trên phiếu XUẤT KHO
            if picking.picking_type_code != 'outgoing':
                continue

            # ================================================================
            # CHỐT CHẶN 1 — Kiểm tra Hạn Sử Dụng (HSD)
            # Chạy TRƯỚC khi kiểm tra tồn kho — đúng thứ tự BPMN
            # ================================================================
            for move in picking.move_ids:
                product = move.product_id
                for move_line in move.move_line_ids:
                    lot = move_line.lot_id
                    if not lot:
                        continue

                    expiration_date = lot.expiration_date
                    if not expiration_date:
                        continue

                    exp_date = expiration_date.date() \
                        if hasattr(expiration_date, 'date') \
                        else expiration_date

                    if exp_date < today:
                        raise ValidationError(_(
                            "🚫 CHỐT CHẶN 1 — THUỐC ĐÃ HẾT HẠN SỬ DỤNG!\n\n"
                            "Sản phẩm : %s\n"
                            "Lô hàng  : %s\n"
                            "Hạn SD   : %s\n"
                            "Hôm nay  : %s\n\n"
                            "➡ Vui lòng quay lại đơn bán hàng (Sale Order)\n"
                            "  để thay đổi sản phẩm hoặc chọn lô còn hạn."
                        ) % (
                            product.display_name,
                            lot.name,
                            exp_date.strftime('%d/%m/%Y'),
                            today.strftime('%d/%m/%Y'),
                        ))

            # ================================================================
            # CHỐT CHẶN 2 — Kiểm tra Tồn kho (Số lượng)
            # Chỉ chạy khi đã vượt qua chốt chặn HSD ở trên
            # ================================================================
            for move in picking.move_ids:
                product = move.product_id
                demand   = move.product_uom_qty   # Số lượng yêu cầu
                reserved = move.reserved_availability  # Số lượng đã giữ chỗ

                if reserved < demand:
                    thieu = demand - reserved
                    raise ValidationError(_(
                        "🚫 CHỐT CHẶN 2 — KHÔNG ĐỦ SỐ LƯỢNG TỒN KHO!\n\n"
                        "Sản phẩm    : %s\n"
                        "Yêu cầu     : %s\n"
                        "Hiện có     : %s\n"
                        "Còn thiếu   : %s\n\n"
                        "➡ Vui lòng quay lại đơn bán hàng (Sale Order)\n"
                        "  để điều chỉnh lại số lượng cho phù hợp."
                    ) % (
                        product.display_name,
                        int(demand),
                        int(reserved),
                        int(thieu),
                    ))

        # ====================================================================
        # Vượt qua cả 2 chốt chặn → Odoo xử lý xuất kho bình thường
        # ====================================================================
        return super(StockPicking, self).action_validate()