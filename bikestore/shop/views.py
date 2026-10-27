import os
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import Q
from django.views.decorators.http import require_POST
from .models import User, Product, Category, Manufacturer, Suppliers, Unit, Orders, Order_Item


def orders_list(request):
    role = request.session.get('role_name', 'Авторизованный пользователь')
    user_id = request.session.get('user_id')
    user = User.objects.get(user_id=user_id) if user_id else None
    orders = Orders.objects.select_related('pickuppoint_id').all().order_by('-order_date')

    context = {
        'orders': orders,
        'role': role,
        'user': user,
    }

    return render(request, 'order_list.html', context)
                                           

def login_views(request):
    if request.session.get('is_authenticated'):
        return redirect('main')
    if request.method == 'POST':
        login_input = request.POST.get('login', '').strip()
        password_input = request.POST.get('password', '').strip()
        user = User.objects.filter(login=login_input, password=password_input).first()
        if user:
            request.session['is_authenticated'] = True
            request.session['user_id'] = user.user_id
            request.session['user_fullname'] = user.full_name
            request.session['role'] = user.role_id.role_name
            request.session['role_id'] = user.role_id.role_id
            return redirect('main')
        else:
            return render(request, 'login.html', {'error': 'Неверный логин или пароль'})
    return render(request, 'login.html')


def main_views(request):
    if not request.session.get('is_authenticated'):
        return redirect('login')

    user_id = request.session.get('user_id')
    user = User.objects.get(user_id=user_id)
    role = request.session.get('role')

    products = Product.objects.select_related(
        'category_id', 'manufacturer_id', 'supplier_id', 'unit_id'
    ).all()

    for p in products:
        p.final_price = round(p.price * (1 - p.discount / 100), 2)

    return render(request, 'main.html', {
        'user': user,
        'role': role,
        'products': products,
    })


def api_products(request):
    if not request.session.get('is_authenticated'):
        return JsonResponse({'error': 'Не авторизован'}, status=401)

    role = request.session.get('role')
    search = request.GET.get('search', '').strip()
    sort = request.GET.get('sort', '')
    order = request.GET.get('order', 'asc')
    discount_filter = request.GET.get('discount_filter', '')

    products = Product.objects.select_related(
        'category_id', 'manufacturer_id', 'supplier_id', 'unit_id'
    ).all()

    if search:
        products = products.filter(
            Q(product_name__icontains=search) |
            Q(description__icontains=search) |
            Q(manufacturer_id__manufacturer_name__icontains=search) |
            Q(supplier_id__supplier_name__icontains=search) |
            Q(category_id__category_name__icontains=search)
        )

    if discount_filter == '0-11.99':
        products = products.filter(discount__gte=0, discount__lte=11.99)
    elif discount_filter == '12-18.99':
        products = products.filter(discount__gte=12, discount__lte=18.99)
    elif discount_filter == '19+':
        products = products.filter(discount__gte=19)

    if sort in ['stock_quantity', 'price', 'discount']:
        prefix = '-' if order == 'desc' else ''
        products = products.order_by(f'{prefix}{sort}')

    for p in products:
        p.final_price = round(p.price * (1 - p.discount / 100), 2)

    html = render_to_string('partials/product_list.html', {
        'products': products,
        'role': role,
    }, request=request)
    return JsonResponse({'html': html})


def product_form_view(request, product_id=None):
    if not request.session.get('is_authenticated'):
        return redirect('login')

    role = request.session.get('role')
    if role != 'Администратор':
        return redirect('main')

    is_edit = product_id is not None
    product = None

    if is_edit:
        product = get_object_or_404(Product, product_id=product_id)

    common_context = {
        'categories': Category.objects.all(),
        'manufacturers': Manufacturer.objects.all(),
        'suppliers': Suppliers.objects.all(),
        'units': Unit.objects.all(),
        'product': product,
    }

    if request.method == 'POST':
        errors = []

        product_name = request.POST.get('product_name', '').strip()
        if not product_name:
            errors.append('Название товара обязательно')

        try:
            price = float(request.POST.get('price', 0))
            if price < 0:
                errors.append('Цена не может быть отрицательной')
        except (ValueError, TypeError):
            errors.append('Некорректная цена')
            price = 0

        try:
            discount = float(request.POST.get('discount', 0) or 0)
            if discount < 0 or discount > 100:
                errors.append('Скидка должна быть от 0 до 100%')
        except (ValueError, TypeError):
            errors.append('Некорректная скидка')
            discount = 0

        try:
            stock_quantity = int(request.POST.get('stock_quantity', 0))
            if stock_quantity < 0:
                errors.append('Количество не может быть отрицательным')
        except (ValueError, TypeError):
            errors.append('Некорректное количество')
            stock_quantity = 0

        category_id = request.POST.get('category_id')
        manufacturer_id = request.POST.get('manufacturer_id')
        supplier_id = request.POST.get('supplier_id')
        unit_id = request.POST.get('unit_id')

        if not category_id:
            errors.append('Выберите категорию')
        if not manufacturer_id:
            errors.append('Выберите производителя')
        if not supplier_id:
            errors.append('Выберите поставщика')
        if not unit_id:
            errors.append('Выберите единицу измерения')

        if errors:
            return render(request, 'product_form.html', {
                **common_context,
                'errors': errors,
            })

        image_path = product.image_path if product else None
        if 'image' in request.FILES:
            if product and product.image_path:
                old_path = os.path.join(settings.BASE_DIR, 'shop', 'static', product.image_path)
                if os.path.exists(old_path):
                    os.remove(old_path)

            image = request.FILES['image']
            upload_dir = os.path.join(settings.BASE_DIR, 'shop', 'static', 'images')
            os.makedirs(upload_dir, exist_ok=True)

            if is_edit:
                filename = f'product_{product.product_id}_{image.name}'
            else:
                last = Product.objects.order_by('-product_id').first()
                new_id = (last.product_id + 1) if last else 1
                filename = f'product_{new_id}_{image.name}'

            filepath = os.path.join(upload_dir, filename)
            with open(filepath, 'wb+') as destination:
                for chunk in image.chunks():
                    destination.write(chunk)
            image_path = f'images/{filename}'

        if is_edit:
            product.product_name = product_name
            product.category_id_id = category_id
            product.description = request.POST.get('description', '')
            product.manufacturer_id_id = manufacturer_id
            product.supplier_id_id = supplier_id
            product.price = price
            product.unit_id_id = unit_id
            product.stock_quantity = stock_quantity
            product.discount = discount
            product.image_path = image_path
            product.save()
        else:
            last = Product.objects.order_by('-product_id').first()
            new_id = (last.product_id + 1) if last else 1

            Product.objects.create(
                product_id=new_id,
                product_name=product_name,
                category_id_id=category_id,
                description=request.POST.get('description', ''),
                manufacturer_id_id=manufacturer_id,
                supplier_id_id=supplier_id,
                price=price,
                unit_id_id=unit_id,
                stock_quantity=stock_quantity,
                discount=discount,
                image_path=image_path,
            )

        return redirect('main')

    return render(request, 'product_form.html', common_context)


@require_POST
def product_delete_view(request, product_id):
    if not request.session.get('is_authenticated'):
        return JsonResponse({'error': 'Не авторизован'}, status=401)
    if request.session.get('role') != 'Администратор':
        return JsonResponse({'error': 'Нет прав'}, status=403)

    product = get_object_or_404(Product, product_id=product_id)

    if Order_Item.objects.filter(product_id=product).exists():
        return JsonResponse({'error': 'Нельзя удалить товар, который есть в заказе'}, status=400)

    if product.image_path:
        full_path = os.path.join(settings.BASE_DIR, 'shop', 'static', product.image_path)
        if os.path.exists(full_path):
            os.remove(full_path)

    product.delete()
    return JsonResponse({'success': True})


def logout_views(request):
    request.session.flush()
    return redirect('login')