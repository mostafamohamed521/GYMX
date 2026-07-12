from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from apps.accounts.permissions import role_required, FRONT_DESK_ROLES
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum, Count
from django.utils import timezone

from .models import Sale, SaleItem, Discount, GiftCard, Return
from apps.inventory.models import Product, ProductCategory, Warehouse, Stock, StockMovement
from apps.members.models import Member


CART_KEY = 'pos_cart'


def _get_cart(request):
    return request.session.get(CART_KEY, [])


def _save_cart(request, cart):
    request.session[CART_KEY] = cart
    request.session.modified = True


def _cart_totals(cart):
    subtotal = sum(item['price'] * item['qty'] for item in cart)
    return subtotal


# ── 1. POS Screen ──────────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def pos_screen(request):
    cart = _get_cart(request)
    products = Product.objects.filter(is_active=True, is_sellable=True).select_related('category')[:60]
    categories = ProductCategory.objects.all()
    subtotal = _cart_totals(cart)

    discount_code = request.session.get('pos_discount_code')
    discount_amount = request.session.get('pos_discount_amount', 0)
    total = subtotal - discount_amount

    return render(request, 'pos/pos_screen.html', {
        'products': products, 'categories': categories,
        'cart': cart, 'subtotal': subtotal,
        'discount_code': discount_code, 'discount_amount': discount_amount,
        'total': total,
        'members': Member.objects.filter(status='active').order_by('first_name'),
    })


# ── 2. Product Catalog ─────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def product_catalog(request):
    products = Product.objects.filter(is_active=True, is_sellable=True).select_related('category')
    q     = request.GET.get('q','')
    cat_f = request.GET.get('category','')
    if q:     products = products.filter(Q(name__icontains=q)|Q(sku__icontains=q))
    if cat_f: products = products.filter(category__pk=cat_f)

    categories = ProductCategory.objects.all()
    return render(request, 'pos/product_catalog.html', {
        'products': products, 'categories': categories, 'q': q, 'cat_f': cat_f,
    })


# ── 3. Shopping Cart (add/remove/clear) ────────────────────
@role_required(*FRONT_DESK_ROLES)
def cart_add(request):
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=request.POST.get('product_id'))
        qty     = int(request.POST.get('qty', 1))
        cart    = _get_cart(request)

        for item in cart:
            if item['product_id'] == product.pk:
                item['qty'] += qty
                _save_cart(request, cart)
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status':'ok','cart_count': sum(i['qty'] for i in cart)})
                return redirect('pos:screen')

        cart.append({
            'product_id': product.pk, 'name': product.name,
            'price': float(product.sale_price), 'qty': qty,
        })
        _save_cart(request, cart)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status':'ok','cart_count': sum(i['qty'] for i in cart)})
    return redirect('pos:screen')


@role_required(*FRONT_DESK_ROLES)
def cart_remove(request, index):
    cart = _get_cart(request)
    if 0 <= index < len(cart):
        cart.pop(index)
        _save_cart(request, cart)
    return redirect('pos:screen')


@role_required(*FRONT_DESK_ROLES)
def cart_clear(request):
    _save_cart(request, [])
    request.session.pop('pos_discount_code', None)
    request.session.pop('pos_discount_amount', None)
    return redirect('pos:screen')


# ── 4. Barcode Scanner ─────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def barcode_scanner(request):
    return render(request, 'pos/barcode_scanner.html', {})


@role_required(*FRONT_DESK_ROLES)
def ajax_scan(request):
    code = request.GET.get('code', '')
    product = Product.objects.filter(barcode=code, is_active=True).first()
    if product:
        return JsonResponse({'found': True, 'id': product.pk, 'name': product.name, 'price': str(product.sale_price)})
    return JsonResponse({'found': False})


@role_required(*FRONT_DESK_ROLES)
def ajax_apply_discount(request):
    code = request.POST.get('code', '').upper()
    cart = _get_cart(request)
    subtotal = _cart_totals(cart)
    discount = Discount.objects.filter(code=code).first()
    if not discount or not discount.is_valid:
        return JsonResponse({'status':'error','message':'Invalid or expired discount code.'})
    amount = discount.calculate_discount(subtotal)
    request.session['pos_discount_code'] = code
    request.session['pos_discount_amount'] = amount
    return JsonResponse({'status':'ok','amount': amount, 'total': subtotal - amount})


# ── 5. Checkout ─────────────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def checkout(request):
    cart = _get_cart(request)
    if not cart:
        messages.warning(request, 'Cart is empty.')
        return redirect('pos:screen')

    subtotal = _cart_totals(cart)
    discount_code = request.session.get('pos_discount_code')
    discount_amount = request.session.get('pos_discount_amount', 0)
    total = subtotal - discount_amount

    if request.method == 'POST':
        try:
            member_pk = request.POST.get('member')
            method    = request.POST.get('payment_method', 'cash')
            received  = float(request.POST.get('amount_received', total))
            wh        = Warehouse.objects.first()

            discount_obj = Discount.objects.filter(code=discount_code).first() if discount_code else None

            sale = Sale.objects.create(
                member=Member.objects.filter(pk=member_pk).first() if member_pk else None,
                warehouse=wh, cashier=request.user,
                subtotal=subtotal, discount_code=discount_obj,
                discount_amount=discount_amount, total=total,
                payment_method=method, amount_received=received,
                change_due=max(received - total, 0),
            )
            for item in cart:
                product = Product.objects.filter(pk=item['product_id']).first()
                SaleItem.objects.create(
                    sale=sale, product=product, product_name=item['name'],
                    quantity=item['qty'], unit_price=item['price'],
                )
                # Deduct stock
                if product and wh:
                    stock, _ = Stock.objects.get_or_create(product=product, warehouse=wh, defaults={'quantity':0})
                    stock.quantity = max(stock.quantity - item['qty'], 0)
                    stock.save()
                    StockMovement.objects.create(
                        product=product, warehouse=wh, move_type='out',
                        quantity=item['qty'], reference=sale.invoice_number,
                        performed_by=request.user,
                    )

            if discount_obj:
                discount_obj.used_count += 1
                discount_obj.save(update_fields=['used_count'])

            _save_cart(request, [])
            request.session.pop('pos_discount_code', None)
            request.session.pop('pos_discount_amount', None)

            messages.success(request, f'Sale {sale.invoice_number} completed!')
            return redirect('pos:sale_detail', pk=sale.pk)
        except Exception as e:
            messages.error(request, f'Error: {e}')

    return render(request, 'pos/checkout.html', {
        'cart': cart, 'subtotal': subtotal, 'discount_amount': discount_amount,
        'total': total, 'members': Member.objects.filter(status='active').order_by('first_name'),
        'payment_methods': Sale.PaymentMethod.choices,
    })


# ── 6. Sales History ────────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def sales_history(request):
    sales = Sale.objects.select_related('member','cashier').order_by('-created_at')
    q        = request.GET.get('q','')
    status_f = request.GET.get('status','')
    if q:        sales = sales.filter(Q(invoice_number__icontains=q)|Q(member__first_name__icontains=q))
    if status_f: sales = sales.filter(status=status_f)

    stats = {
        'total':   sales.count(),
        'revenue': Sale.objects.filter(status='completed').aggregate(t=Sum('total'))['t'] or 0,
        'today':   Sale.objects.filter(created_at__date=date.today()).count(),
    }
    return render(request, 'pos/sales_history.html', {
        'sales': sales[:100], 'stats': stats, 'q': q, 'status_f': status_f,
        'statuses': Sale.Status.choices,
    })


@role_required(*FRONT_DESK_ROLES)
def sale_detail(request, pk):
    sale = get_object_or_404(Sale.objects.select_related('member','cashier','discount_code').prefetch_related('items'), pk=pk)
    return render(request, 'pos/sale_detail.html', {'sale': sale})


# ── 7. Returns ───────────────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def returns(request):
    return_list = Return.objects.select_related('sale','sale_item','processed_by').order_by('-created_at')
    stats = {
        'total':  return_list.count(),
        'amount': return_list.aggregate(t=Sum('refund_amount'))['t'] or 0,
    }
    return render(request, 'pos/returns.html', {'return_list': return_list, 'stats': stats})


@role_required(*FRONT_DESK_ROLES)
def return_new(request, sale_pk):
    sale = get_object_or_404(Sale.objects.prefetch_related('items'), pk=sale_pk)

    if request.method == 'POST':
        item_pk = request.POST.get('sale_item')
        item    = get_object_or_404(SaleItem, pk=item_pk, sale=sale)
        qty     = int(request.POST.get('quantity', 1))
        refund  = float(item.unit_price) * qty

        Return.objects.create(
            sale=sale, sale_item=item, quantity=qty,
            reason=request.POST.get('reason','other'),
            refund_amount=refund, notes=request.POST.get('notes',''),
            processed_by=request.user,
        )
        item.returned_qty += qty
        item.is_returned = item.returned_qty >= item.quantity
        item.save()

        # Restock
        if item.product and sale.warehouse:
            stock, _ = Stock.objects.get_or_create(product=item.product, warehouse=sale.warehouse, defaults={'quantity':0})
            stock.quantity += qty
            stock.save()
            StockMovement.objects.create(
                product=item.product, warehouse=sale.warehouse, move_type='in',
                quantity=qty, reference=f'Return — {sale.invoice_number}', performed_by=request.user,
            )

        all_returned = all(i.is_returned for i in sale.items.all())
        sale.status = 'refunded' if all_returned else 'partial_refund'
        sale.save(update_fields=['status'])

        messages.success(request, f'Return processed — {refund:.0f} EGP refunded.')
        return redirect('pos:returns')

    return render(request, 'pos/return_form.html', {
        'sale': sale, 'reasons': Return.Reason.choices,
    })


# ── 8. Daily Sales ───────────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def daily_sales(request):
    day = request.GET.get('date', str(date.today()))
    sales = Sale.objects.filter(created_at__date=day, status='completed').select_related('member','cashier')

    stats = {
        'total_sales':  sales.count(),
        'revenue':      sales.aggregate(t=Sum('total'))['t'] or 0,
        'items_sold':   SaleItem.objects.filter(sale__in=sales).aggregate(t=Sum('quantity'))['t'] or 0,
    }
    method_breakdown = sales.values('payment_method').annotate(total=Sum('total'), count=Count('id'))

    return render(request, 'pos/daily_sales.html', {
        'sales': sales, 'stats': stats, 'method_breakdown': method_breakdown, 'day': day,
    })


# ── 9. Categories (POS view of product categories) ──────────
@role_required(*FRONT_DESK_ROLES)
def pos_categories(request):
    cats = ProductCategory.objects.annotate(
        prod_count=Count('products', filter=Q(products__is_sellable=True))
    ).order_by('name')
    return render(request, 'pos/categories.html', {'cats': cats})


# ── 10. Discounts ─────────────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def discounts(request):
    if request.method == 'POST':
        Discount.objects.create(
            code=request.POST.get('code','').upper(),
            description=request.POST.get('description',''),
            discount_type=request.POST.get('discount_type','percent'),
            value=float(request.POST.get('value',0)),
            valid_from=request.POST.get('valid_from') or date.today(),
            valid_until=request.POST.get('valid_until') or None,
            max_uses=request.POST.get('max_uses') or None,
        )
        messages.success(request, 'Discount code created.')
        return redirect('pos:discounts')

    discount_list = Discount.objects.order_by('-created_at')
    return render(request, 'pos/discounts.html', {
        'discount_list': discount_list, 'today': date.today(),
        'types': Discount.DiscountType.choices,
    })


# ── 11. Gift Cards ────────────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def gift_cards(request):
    cards = GiftCard.objects.select_related('purchased_by').order_by('-created_at')
    stats = {
        'total':    cards.count(),
        'active':   cards.filter(status='active').count(),
        'balance':  cards.filter(status='active').aggregate(t=Sum('balance'))['t'] or 0,
    }
    return render(request, 'pos/gift_cards.html', {'cards': cards, 'stats': stats})


@role_required(*FRONT_DESK_ROLES)
def gift_card_new(request):
    if request.method == 'POST':
        member_pk = request.POST.get('purchased_by')
        amount = float(request.POST.get('initial_amount', 0))
        GiftCard.objects.create(
            initial_amount=amount, balance=amount,
            purchased_by=Member.objects.filter(pk=member_pk).first() if member_pk else None,
            issued_to=request.POST.get('issued_to',''),
            expiry_date=request.POST.get('expiry_date') or None,
            created_by=request.user,
        )
        messages.success(request, 'Gift card created!')
        return redirect('pos:gift_cards')

    members = Member.objects.filter(status='active').order_by('first_name')
    return render(request, 'pos/gift_card_form.html', {'members': members, 'today': date.today()})
