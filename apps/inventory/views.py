from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count

from .models import (
    Product, ProductCategory, Brand, Equipment, EquipmentMaintenance,
    Stock, Warehouse, StockMovement, DamagedItem,
    PurchaseOrder, PurchaseOrderItem, Supplier,
)


@login_required
def products(request):
    prods = Product.objects.select_related('category','brand').filter(is_active=True)
    q     = request.GET.get('q','')
    cat_f = request.GET.get('category','')
    if q:     prods = prods.filter(Q(name__icontains=q)|Q(sku__icontains=q))
    if cat_f: prods = prods.filter(category__pk=cat_f)

    stats = {
        'total':     Product.objects.filter(is_active=True).count(),
        'low_stock': sum(1 for p in Product.objects.filter(is_active=True) if p.is_low_stock),
        'categories':ProductCategory.objects.count(),
        'value':     sum(float(p.cost_price) * p.total_stock for p in Product.objects.filter(is_active=True)),
    }
    cats = ProductCategory.objects.all()
    return render(request, 'inventory/products.html', {
        'prods': prods, 'stats': stats, 'cats': cats, 'q': q, 'cat_f': cat_f,
    })


@login_required
def product_new(request):
    if request.method == 'POST':
        try:
            cat_pk   = request.POST.get('category')
            brand_pk = request.POST.get('brand')
            p = Product(
                name        = request.POST.get('name'),
                category    = ProductCategory.objects.filter(pk=cat_pk).first() if cat_pk else None,
                brand       = Brand.objects.filter(pk=brand_pk).first() if brand_pk else None,
                unit        = request.POST.get('unit','pcs'),
                cost_price  = float(request.POST.get('cost_price',0)),
                sale_price  = float(request.POST.get('sale_price',0)),
                reorder_level = int(request.POST.get('reorder_level',10)),
                description = request.POST.get('description',''),
                barcode     = request.POST.get('barcode',''),
                is_sellable = bool(request.POST.get('is_sellable')),
                created_by  = request.user,
            )
            if 'image' in request.FILES:
                p.image = request.FILES['image']
            p.save()

            wh_pk = request.POST.get('warehouse')
            qty   = int(request.POST.get('initial_qty', 0))
            if wh_pk and qty:
                wh = Warehouse.objects.filter(pk=wh_pk).first()
                Stock.objects.create(product=p, warehouse=wh, quantity=qty)
                StockMovement.objects.create(product=p, warehouse=wh, move_type='in', quantity=qty, reference='Initial stock', performed_by=request.user)

            messages.success(request, f'Product "{p.name}" added!')
            return redirect('inventory:products')
        except Exception as e:
            messages.error(request, f'Error: {e}')

    return render(request, 'inventory/product_form.html', {
        'cats': ProductCategory.objects.all(),
        'brands': Brand.objects.all(),
        'warehouses': Warehouse.objects.all(),
        'units': Product.Unit.choices,
    })


@login_required
def categories(request):
    if request.method == 'POST':
        ProductCategory.objects.create(
            name=request.POST.get('name'),
            icon=request.POST.get('icon','fa-box'),
            color=request.POST.get('color','#3B82F6'),
        )
        messages.success(request, 'Category added.')
        return redirect('inventory:categories')

    cats = ProductCategory.objects.annotate(prod_count=Count('products')).order_by('name')
    return render(request, 'inventory/categories.html', {'cats': cats})


@login_required
def brands(request):
    if request.method == 'POST':
        Brand.objects.create(name=request.POST.get('name'), website=request.POST.get('website',''))
        messages.success(request, 'Brand added.')
        return redirect('inventory:brands')

    brand_list = Brand.objects.annotate(prod_count=Count('products')).order_by('name')
    return render(request, 'inventory/brands.html', {'brand_list': brand_list})


@login_required
def equipment_list(request):
    equipment = Equipment.objects.select_related('category','brand').all()
    status_f  = request.GET.get('status','')
    if status_f: equipment = equipment.filter(status=status_f)

    stats = {
        'total':        Equipment.objects.count(),
        'operational':  Equipment.objects.filter(status='operational').count(),
        'maintenance':  Equipment.objects.filter(status='maintenance').count(),
        'broken':       Equipment.objects.filter(status='broken').count(),
    }
    return render(request, 'inventory/equipment_list.html', {
        'equipment': equipment, 'stats': stats, 'status_f': status_f,
        'statuses': Equipment.Status.choices,
    })


@login_required
def equipment_new(request):
    if request.method == 'POST':
        try:
            cat_pk   = request.POST.get('category')
            brand_pk = request.POST.get('brand')
            eq = Equipment(
                name          = request.POST.get('name'),
                category      = ProductCategory.objects.filter(pk=cat_pk).first() if cat_pk else None,
                brand         = Brand.objects.filter(pk=brand_pk).first() if brand_pk else None,
                serial_number = request.POST.get('serial_number',''),
                purchase_date = request.POST.get('purchase_date') or None,
                purchase_price= float(request.POST.get('purchase_price',0)),
                warranty_until= request.POST.get('warranty_until') or None,
                location      = request.POST.get('location',''),
                status        = request.POST.get('status','operational'),
                notes         = request.POST.get('notes',''),
            )
            if 'image' in request.FILES:
                eq.image = request.FILES['image']
            eq.save()
            messages.success(request, f'Equipment "{eq.name}" added!')
            return redirect('inventory:equipment_detail', pk=eq.pk)
        except Exception as e:
            messages.error(request, f'Error: {e}')

    return render(request, 'inventory/equipment_form.html', {
        'cats': ProductCategory.objects.all(),
        'brands': Brand.objects.all(),
        'statuses': Equipment.Status.choices,
        'today': date.today(),
    })


@login_required
def equipment_detail(request, pk):
    eq = get_object_or_404(Equipment.objects.select_related('category','brand'), pk=pk)
    maintenance = eq.maintenance_records.all()[:10]
    return render(request, 'inventory/equipment_detail.html', {
        'eq': eq, 'maintenance': maintenance, 'today': date.today(),
    })


@login_required
def equipment_maintenance(request):
    if request.method == 'POST':
        eq = get_object_or_404(Equipment, pk=request.POST.get('equipment'))
        EquipmentMaintenance.objects.create(
            equipment=eq,
            maintenance_type=request.POST.get('maintenance_type','routine'),
            scheduled_date=request.POST.get('scheduled_date'),
            cost=float(request.POST.get('cost',0)),
            technician=request.POST.get('technician',''),
            notes=request.POST.get('notes',''),
        )
        eq.status = 'maintenance'
        eq.save(update_fields=['status'])
        messages.success(request, f'Maintenance scheduled for {eq.name}.')
        return redirect('inventory:maintenance')

    upcoming = EquipmentMaintenance.objects.filter(status='scheduled').select_related('equipment').order_by('scheduled_date')
    equipment = Equipment.objects.all()
    return render(request, 'inventory/equipment_maintenance.html', {
        'upcoming': upcoming, 'equipment': equipment,
        'types': EquipmentMaintenance.MaintenanceType.choices, 'today': date.today(),
    })


@login_required
def maintenance_history(request):
    history = EquipmentMaintenance.objects.select_related('equipment').filter(status='completed').order_by('-completed_date')
    return render(request, 'inventory/maintenance_history.html', {'history': history})


@login_required
def inventory_stock(request):
    stocks = Stock.objects.select_related('product','warehouse')
    wh_f   = request.GET.get('warehouse','')
    if wh_f: stocks = stocks.filter(warehouse__pk=wh_f)

    warehouses = Warehouse.objects.all()
    stats = {
        'total_products': Product.objects.filter(is_active=True).count(),
        'total_stock':    stocks.aggregate(t=Sum('quantity'))['t'] or 0,
        'warehouses':     Warehouse.objects.count(),
    }
    return render(request, 'inventory/stock.html', {
        'stocks': stocks, 'warehouses': warehouses, 'stats': stats, 'wh_f': wh_f,
    })


@login_required
def warehouses(request):
    if request.method == 'POST':
        Warehouse.objects.create(name=request.POST.get('name'), location=request.POST.get('location',''))
        messages.success(request, 'Warehouse added.')
        return redirect('inventory:warehouses')

    wh_list = Warehouse.objects.annotate(
        stock_count=Count('stock_entries')
    ).order_by('name')
    return render(request, 'inventory/warehouses.html', {'wh_list': wh_list})


@login_required
def stock_movement(request):
    if request.method == 'POST':
        product   = get_object_or_404(Product, pk=request.POST.get('product'))
        warehouse = get_object_or_404(Warehouse, pk=request.POST.get('warehouse'))
        move_type = request.POST.get('move_type','in')
        qty       = int(request.POST.get('quantity',0))

        StockMovement.objects.create(
            product=product, warehouse=warehouse, move_type=move_type,
            quantity=qty, reference=request.POST.get('reference',''),
            notes=request.POST.get('notes',''), performed_by=request.user,
        )
        stock, _ = Stock.objects.get_or_create(product=product, warehouse=warehouse, defaults={'quantity':0})
        if move_type in ('in',):
            stock.quantity += qty
        elif move_type in ('out','damage'):
            stock.quantity = max(stock.quantity - qty, 0)
        elif move_type == 'adjust':
            stock.quantity = qty
        stock.save()

        messages.success(request, f'Stock movement recorded for {product.name}.')
        return redirect('inventory:movement')

    movements = StockMovement.objects.select_related('product','warehouse').order_by('-created_at')[:100]
    products_qs = Product.objects.filter(is_active=True).order_by('name')
    warehouses_qs = Warehouse.objects.all()
    return render(request, 'inventory/stock_movement.html', {
        'movements': movements, 'products': products_qs, 'warehouses': warehouses_qs,
        'move_types': StockMovement.MoveType.choices,
    })


@login_required
def low_stock(request):
    low_products = [p for p in Product.objects.filter(is_active=True).select_related('category') if p.is_low_stock]
    return render(request, 'inventory/low_stock.html', {'low_products': low_products})


@login_required
def damaged_items(request):
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=request.POST.get('product'))
        wh_pk   = request.POST.get('warehouse')
        DamagedItem.objects.create(
            product=product,
            warehouse=Warehouse.objects.filter(pk=wh_pk).first() if wh_pk else None,
            quantity=int(request.POST.get('quantity',1)),
            reason=request.POST.get('reason',''),
            reported_by=request.user,
        )
        messages.success(request, 'Damaged item recorded.')
        return redirect('inventory:damaged')

    items = DamagedItem.objects.select_related('product','warehouse').order_by('-reported_at')
    products_qs = Product.objects.filter(is_active=True).order_by('name')
    warehouses_qs = Warehouse.objects.all()
    return render(request, 'inventory/damaged_items.html', {
        'items': items, 'products': products_qs, 'warehouses': warehouses_qs,
    })


@login_required
def purchase_orders(request):
    orders = PurchaseOrder.objects.select_related('supplier','warehouse').order_by('-order_date')
    status_f = request.GET.get('status','')
    if status_f: orders = orders.filter(status=status_f)
    stats = {
        'total':    PurchaseOrder.objects.count(),
        'pending':  PurchaseOrder.objects.filter(status='ordered').count(),
        'value':    PurchaseOrder.objects.aggregate(t=Sum('total_amount'))['t'] or 0,
    }
    return render(request, 'inventory/purchase_orders.html', {
        'orders': orders, 'stats': stats, 'status_f': status_f,
        'statuses': PurchaseOrder.Status.choices,
    })


@login_required
def po_new(request):
    if request.method == 'POST':
        try:
            supplier = get_object_or_404(Supplier, pk=request.POST.get('supplier'))
            wh_pk    = request.POST.get('warehouse')
            po = PurchaseOrder.objects.create(
                supplier=supplier,
                warehouse=Warehouse.objects.filter(pk=wh_pk).first() if wh_pk else None,
                order_date=request.POST.get('order_date') or date.today(),
                expected_date=request.POST.get('expected_date') or None,
                notes=request.POST.get('notes',''),
                created_by=request.user,
            )
            prod_ids = request.POST.getlist('product_ids')
            total = 0
            for pid in prod_ids:
                prod  = Product.objects.filter(pk=pid).first()
                qty   = int(request.POST.get(f'qty_{pid}',1))
                price = float(request.POST.get(f'price_{pid}', prod.cost_price if prod else 0))
                if prod:
                    PurchaseOrderItem.objects.create(po=po, product=prod, quantity=qty, unit_price=price)
                    total += qty * price
            po.total_amount = total
            po.save(update_fields=['total_amount'])
            messages.success(request, f'{po.po_number} created!')
            return redirect('inventory:purchase_orders')
        except Exception as e:
            messages.error(request, f'Error: {e}')

    return render(request, 'inventory/po_form.html', {
        'suppliers': Supplier.objects.filter(is_active=True),
        'warehouses': Warehouse.objects.all(),
        'products': Product.objects.filter(is_active=True).order_by('name'),
        'today': date.today(),
    })


@login_required
def suppliers(request):
    if request.method == 'POST':
        Supplier.objects.create(
            name=request.POST.get('name'),
            contact_person=request.POST.get('contact_person',''),
            phone=request.POST.get('phone',''),
            email=request.POST.get('email',''),
            address=request.POST.get('address',''),
        )
        messages.success(request, 'Supplier added.')
        return redirect('inventory:suppliers')

    supplier_list = Supplier.objects.annotate(po_count=Count('purchase_orders')).order_by('name')
    return render(request, 'inventory/suppliers.html', {'supplier_list': supplier_list})


@login_required
def supplier_detail(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    orders   = PurchaseOrder.objects.filter(supplier=supplier).order_by('-order_date')
    return render(request, 'inventory/supplier_detail.html', {'supplier': supplier, 'orders': orders})


@login_required
def warranty_tracking(request):
    today = date.today()
    equipment = Equipment.objects.filter(warranty_until__isnull=False).order_by('warranty_until')
    expiring  = [e for e in equipment if e.warranty_expiring_soon]
    expired   = equipment.filter(warranty_until__lt=today)
    active    = equipment.filter(warranty_until__gte=today)

    return render(request, 'inventory/warranty.html', {
        'expiring': expiring, 'expired': expired, 'active': active, 'today': today,
    })
