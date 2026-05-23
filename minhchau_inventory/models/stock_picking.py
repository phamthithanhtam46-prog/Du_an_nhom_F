# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _sanity_check(self, separate_pickings=True):
        """
        Override _sanity_check() — chạy TRƯỚC khi Odoo kiểm tra Lot.
        Chèn 2 chốt chặn theo BPMN Nhà thuốc Minh Châu:
            [1] Quét lot của product → HSD hết hạn? → CHẶN
            [2] Kiểm tra số lượng   → Không đủ?    → CHẶN
            [3] super()._sanity_check() → Odoo kiểm tra bình thường
        """
        today = date.today()

        for picking in self:
            if picking.picking_type_code != 'outgoing':
                continue

            # Lấy Sale Order liên quan
            sale_order = getattr(picking, 'sale_id', None)
            so_name = sale_order.name if sale_order else None

            for move in picking.move_ids:
                product = move.product_id

                # ============================================================
                # CHỐT CHẶN 1 — Quét tất cả Lot của product trong kho
                # ============================================================
                lots = self.env['stock.lot'].search([
                    ('product_id', '=', product.id),
                    ('company_id', '=', picking.company_id.id),
                ])

                if lots:
                    lots_with_stock = lots.filtered(
                        lambda l: l.product_qty > 0
                    )

                    if lots_with_stock:
                        valid_lots = lots_with_stock.filtered(
                            lambda l: not l.expiration_date or
                            (l.expiration_date.date()
                             if hasattr(l.expiration_date, 'date')
                             else l.expiration_date) >= today
                        )

                        expired_lots = lots_with_stock.filtered(
                            lambda l: l.expiration_date and
                            (l.expiration_date.date()
                             if hasattr(l.expiration_date, 'date')
                             else l.expiration_date) < today
                        )

                        if expired_lots and not valid_lots:
                            exp_list = '\n'.join([
                                '  • %s — Expired: %s' % (
                                    l.name,
                                    (l.expiration_date.date()
                                     if hasattr(l.expiration_date, 'date')
                                     else l.expiration_date
                                    ).strftime('%d/%m/%Y')
                                )
                                for l in expired_lots
                            ])
                            msg = (
                                "🔴 BLOCKED — ALL LOTS EXPIRED\n\n"
                                "Product : %s\n\n"
                                "Expired lots in stock:\n%s\n\n"
                            ) % (product.display_name, exp_list)
                            if so_name:
                                msg += "➡ Please return to Sale Order %s\n" \
                                       "  and replace with a valid product." % so_name
                            else:
                                msg += "➡ Please select a valid product."
                            raise ValidationError(_(msg))

                # ============================================================
                # CHỐT CHẶN 2 — Kiểm tra số lượng tồn kho
                # ============================================================
                if lots:
                    available_qty = sum(
                        l.product_qty for l in lots.filtered(
                            lambda l: not l.expiration_date or
                            (l.expiration_date.date()
                             if hasattr(l.expiration_date, 'date')
                             else l.expiration_date) >= today
                        )
                    )
                else:
                    available_qty = product.with_context(
                        location=picking.location_id.id
                    ).qty_available

                demand_qty = move.product_uom_qty

                if available_qty < demand_qty:
                    msg = (
                        "🟠 BLOCKED — INSUFFICIENT QUANTITY\n\n"
                        "Product    : %s\n"
                        "Demand     : %s\n"
                        "Available  : %s\n"
                        "Shortage   : %s\n\n"
                    ) % (
                        product.display_name,
                        int(demand_qty),
                        int(available_qty),
                        int(demand_qty - available_qty),
                    )
                    if so_name:
                        msg += "➡ Please return to Sale Order %s\n" \
                               "  and adjust the quantity accordingly." % so_name
                    else:
                        msg += "➡ Please adjust the quantity in the related Sale Order."
                    raise ValidationError(_(msg))

        return super(StockPicking, self)._sanity_check(
            separate_pickings=separate_pickings
        )