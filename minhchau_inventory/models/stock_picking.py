# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date


class StockPicking(models.Model):
    """
    Kế thừa stock.picking — 2 chốt chặn theo BPMN Nhà thuốc Minh Châu:
        [1] Kiểm tra HSD       → Expired        → chặn + ghi rõ Sale Order
        [2] Kiểm tra tồn kho   → Insufficient   → chặn + ghi rõ Sale Order
        [3] Xuất kho bình thường
    """
    _inherit = 'stock.picking'

    def action_validate(self):
        today = date.today()

        for picking in self:
            if picking.picking_type_code != 'outgoing':
                continue

            # Lấy tên Sale Order liên quan (nếu có)
            sale_order = getattr(picking, 'sale_id', None)
            so_name = sale_order.name if sale_order else None

            # ============================================================
            # CHỐT CHẶN 1 — Expired (HSD)
            # ============================================================
            for move in picking.move_ids:
                for ml in move.move_line_ids:
                    lot = ml.lot_id
                    if not lot or not lot.expiration_date:
                        continue
                    exp = lot.expiration_date.date() \
                        if hasattr(lot.expiration_date, 'date') \
                        else lot.expiration_date
                    if exp < today:
                        msg = (
                            "🔴 BLOCKED — EXPIRED PRODUCT\n\n"
                            "Product    : %s\n"
                            "Lot        : %s\n"
                            "Expired on : %s\n"
                            "Today      : %s\n\n"
                        ) % (
                            move.product_id.display_name,
                            lot.name,
                            exp.strftime('%d/%m/%Y'),
                            today.strftime('%d/%m/%Y'),
                        )
                        if so_name:
                            msg += "➡ Please return to Sale Order %s\n" \
                                   "  and replace with a valid product/lot." % so_name
                        else:
                            msg += "➡ Please select a valid lot or replace the product."
                        raise ValidationError(_(msg))

            # ============================================================
            # CHỐT CHẶN 2 — Insufficient Qty (Tồn kho)
            # Odoo 17: dùng 'quantity' thay vì 'reserved_availability'
            # ============================================================
            for move in picking.move_ids:
                # quantity = số lượng thực tế đã điền vào move lines
                # product_uom_qty = số lượng yêu cầu ban đầu
                done_qty   = sum(ml.quantity for ml in move.move_line_ids)
                demand_qty = move.product_uom_qty

                if done_qty < demand_qty:
                    msg = (
                        "🟠 BLOCKED — INSUFFICIENT QUANTITY\n\n"
                        "Product    : %s\n"
                        "Demand     : %s\n"
                        "Available  : %s\n"
                        "Shortage   : %s\n\n"
                    ) % (
                        move.product_id.display_name,
                        int(demand_qty),
                        int(done_qty),
                        int(demand_qty - done_qty),
                    )
                    if so_name:
                        msg += "➡ Please return to Sale Order %s\n" \
                               "  and adjust the quantity accordingly." % so_name
                    else:
                        msg += "➡ Please adjust the quantity in the related Sale Order."
                    raise ValidationError(_(msg))

        return super(StockPicking, self).action_validate()