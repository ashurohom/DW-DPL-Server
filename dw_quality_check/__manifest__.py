{
    'name': 'DW Quality Check',
    'version': '1.0.0',
    'summary': 'Quality checklist for incoming shipments (stock pickings)',
    'category': 'Inventory/Quality',
    'author': 'Dreamwarez',
    'license': 'LGPL-3',
    'depends': ['stock', 'product', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/quality_check.xml',
        'views/stock_picking.xml',
        
    ],
    'installable': True,
    'application': False,
}