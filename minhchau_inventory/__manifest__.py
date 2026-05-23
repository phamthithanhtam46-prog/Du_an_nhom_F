# -*- coding: utf-8 -*-
{
    'name': 'Minh Chau Inventory',
    'version': '1.0.0',
    'summary': 'Tùy chỉnh phân hệ Kho cho Nhà thuốc Minh Châu',
    'description': """
        Module tùy chỉnh phân hệ Kho (Inventory) cho Nhà thuốc Minh Châu.
        Các tính năng chính:
        - Kiểm tra Hạn Sử Dụng (HSD) trước khi xác nhận phiếu kho
        - Chặn ValidationError nếu lô thuốc đã hết hạn
        - Hiển thị Banner Y tế nhắc nhở Dược sĩ kiểm tra HSD và số lượng
    """,
    'author': 'Nhóm F - Tam_Inventory',
    'category': 'Inventory',
    'depends': [
        'stock',          # Phân hệ Kho cốt lõi của Odoo
        'product',        # Quản lý sản phẩm / thuốc
    ],
    'data': [
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}