# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _check_minhchau_errors(self):
        now = fields.Datetime.now()
        expired_lines = []
        insufficient_lines = []

        for move in self.move_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
            product = move.product_id
            qty_demand = move.product_uom_qty

            # ── KIỂM TRA HẠN SỬ DỤNG ──────────────────────────────────────────
            # Chỉ kiểm tra sản phẩm có tracking theo lot/serial
            if product.tracking and product.tracking != 'none':

                # Ưu tiên 1: kiểm tra lot đã được chỉ định trong move line
                if move.move_line_ids:
                    for ml in move.move_line_ids:
                        lot = ml.lot_id
                        if lot and lot.expiration_date and lot.expiration_date < now:
                            expired_lines.append(
                                f"• {product.display_name} | Lot: {lot.name} | HSD: "
                                f"{lot.expiration_date.strftime('%d/%m/%Y')}"
                            )

                else:
                    # Ưu tiên 2: chưa chọn lot → kiểm tra lot khả dụng trong kho
                    quants = self.env['stock.quant'].search([
                        ('product_id', '=', product.id),
                        ('location_id', 'child_of', self.location_id.id),
                        ('quantity', '>', 0),
                    ])
                    lots_in_stock = quants.mapped('lot_id').filtered(lambda l: l)

                    if lots_in_stock:
                        # Nếu TẤT CẢ lot trong kho đều đã hết hạn → cảnh báo
                        all_expired = all(
                            l.expiration_date and l.expiration_date < now
                            for l in lots_in_stock
                        )
                        if all_expired:
                            for lot in lots_in_stock:
                                expired_lines.append(
                                    f"• {product.display_name} | Lot: {lot.name} | HSD: "
                                    f"{lot.expiration_date.strftime('%d/%m/%Y') if lot.expiration_date else 'N/A'}"
                                )

            # ── KIỂM TRA SỐ LƯỢNG TỒN KHO ────────────────────────────────────
            qty_available = product.with_context(
                location=self.location_id.id
            ).qty_available

            if qty_available < qty_demand:
                insufficient_lines.append(
                    f"• {product.display_name} | Yêu cầu: {qty_demand} | Tồn kho: {qty_available}"
                )

        # ── TẠO WIZARD THEO THỨ TỰ ƯU TIÊN ──────────────────────────────────
        # Hết hạn ưu tiên hơn thiếu số lượng
        if expired_lines:
            return self._create_error_wizard(
                title='❌ THUỐC ĐÃ HẾT HẠN SỬ DỤNG',
                error_type='expired',
                message="THUỐC ĐÃ HẾT HẠN SỬ DỤNG\n\n" + "\n".join(expired_lines),
                window_title='Lỗi: Thuốc Hết Hạn Sử Dụng',
            )

        if insufficient_lines:
            return self._create_error_wizard(
                title='❌ KHÔNG ĐỦ SỐ LƯỢNG TỒN KHO',
                error_type='insufficient',
                message="KHÔNG ĐỦ SỐ LƯỢNG TỒN KHO\n\n" + "\n".join(insufficient_lines),
                window_title='Lỗi: Không Đủ Tồn Kho',
            )

        return None

    def _create_error_wizard(self, title, error_type, message, window_title):
        sale_order = self.sale_id
        wizard = self.env['minhchau.stock.error.wizard'].create({
            'title': title,
            'error_type': error_type,
            'message': message,
            'picking_id': self.id,
            'sale_order_id': sale_order.id if sale_order else False,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': window_title,
            'res_model': 'minhchau.stock.error.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def button_validate(self):
        self.ensure_one()

        if self.picking_type_code != 'outgoing':
            return super().button_validate()

        if self.env.context.get('skip_minhchau_check'):
            return super().button_validate()

        error_action = self._check_minhchau_errors()
        if error_action:
            return error_action

        return super(StockPicking, self.with_context(
            skip_sanity_check=True,
            skip_backorder=True,
            skip_sms=True,
        )).button_validate()