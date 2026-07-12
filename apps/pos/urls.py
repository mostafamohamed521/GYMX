from django.urls import path
from . import views

app_name = 'pos'

urlpatterns = [
    path('',                              views.pos_screen,           name='screen'),
    path('catalog/',                      views.product_catalog,      name='catalog'),
    path('cart/add/',                     views.cart_add,             name='cart_add'),
    path('cart/remove/<int:index>/',      views.cart_remove,          name='cart_remove'),
    path('cart/clear/',                   views.cart_clear,           name='cart_clear'),
    path('scanner/',                      views.barcode_scanner,      name='scanner'),
    path('checkout/',                     views.checkout,             name='checkout'),
    path('sales/',                        views.sales_history,        name='sales'),
    path('sales/<int:pk>/',               views.sale_detail,          name='sale_detail'),
    path('returns/',                      views.returns,              name='returns'),
    path('returns/new/<int:sale_pk>/',    views.return_new,           name='return_new'),
    path('daily/',                        views.daily_sales,          name='daily'),
    path('categories/',                   views.pos_categories,       name='categories'),
    path('discounts/',                    views.discounts,            name='discounts'),
    path('gift-cards/',                   views.gift_cards,           name='gift_cards'),
    path('gift-cards/new/',               views.gift_card_new,        name='gift_card_new'),

    # AJAX
    path('ajax/scan/',                    views.ajax_scan,            name='ajax_scan'),
    path('ajax/apply-discount/',          views.ajax_apply_discount, name='ajax_apply_discount'),
]
