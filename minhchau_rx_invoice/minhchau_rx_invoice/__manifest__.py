{
    'name': 'Nhà Thuốc Minh Châu - Xác Nhận Rx',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Yêu cầu Dược sĩ xác nhận đơn thuốc Rx trước khi tạo hóa đơn từ Sales Order',
    'description': """
        Tính năng:
        - Bắt buộc chọn có phải đơn thuốc Rx không khi tạo hóa đơn từ Sales Order.
        - Nếu là đơn thuốc Rx, yêu cầu Dược sĩ xác nhận đủ điều kiện bán.
        - Lưu trữ thông tin xác nhận Rx vào Sales Order và Invoice.
    """,
    'author': 'Minh Châu Pharmacy',
    'depends': ['sale', 'sale_management', 'account'],
    'data': [
        'views/sale_advance_payment_inv_views.xml',
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
