# -*- coding: utf-8 -*-
{
    'name': 'Minh Chau Inventory',
    'version': '1.0.0',
    'summary': 'Tùy chỉnh phân hệ Kho cho Nhà thuốc Minh Châu',
    'description': """
        Module tùy chỉnh phân hệ Kho (Inventory) cho Nhà thuốc Minh Châu.
        - Kiểm tra Hạn Sử Dụng (HSD) trước khi xác nhận phiếu kho
        - Chặn nếu lô thuốc đã hết hạn
        - Chặn nếu không đủ số lượng tồn kho
        - Popup lỗi có nút "Go to Sale Order" để điều chỉnh
        - Banner Y tế nhắc nhở Dược sĩ
    """,
    'author': 'Nhóm F - Tam_Inventory',
    'category': 'Inventory',
    'depends': [
        'stock',
        'product',
        'product_expiry',
        'sale_stock',
        'sale_management',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_error_wizard_views.xml',
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}