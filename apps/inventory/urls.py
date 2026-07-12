from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('',                              views.products,              name='products'),
    path('products/new/',                 views.product_new,           name='product_new'),
    path('categories/',                   views.categories,            name='categories'),
    path('brands/',                       views.brands,                name='brands'),

    path('equipment/',                    views.equipment_list,        name='equipment'),
    path('equipment/new/',                views.equipment_new,         name='equipment_new'),
    path('equipment/<int:pk>/',           views.equipment_detail,      name='equipment_detail'),
    path('equipment/maintenance/',        views.equipment_maintenance, name='maintenance'),
    path('equipment/maintenance/history/', views.maintenance_history,  name='maintenance_history'),

    path('stock/',                        views.inventory_stock,       name='stock'),
    path('warehouses/',                   views.warehouses,            name='warehouses'),
    path('stock/movement/',               views.stock_movement,        name='movement'),
    path('stock/low/',                    views.low_stock,             name='low_stock'),
    path('stock/damaged/',                views.damaged_items,         name='damaged'),

    path('purchase-orders/',              views.purchase_orders,       name='purchase_orders'),
    path('purchase-orders/new/',          views.po_new,                name='po_new'),
    path('suppliers/',                    views.suppliers,             name='suppliers'),
    path('suppliers/<int:pk>/',           views.supplier_detail,       name='supplier_detail'),

    path('warranty/',                     views.warranty_tracking,     name='warranty'),
]
