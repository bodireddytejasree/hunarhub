from datetime import timedelta
from decimal import Decimal, InvalidOperation
from functools import wraps

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Avg, Count, F, ProtectedError, Q, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (ComplaintForm, OrderForm, ProductForm, ProfileForm, ReviewForm,
                    ServiceForm, ServiceRequestForm)
from .models import (Category, Complaint, EntrepreneurProfile, Order, Product, Review,
                     Service, ServiceRequest)

User = get_user_model()


# ---------- access helpers ----------
def role_required(check):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not check(request.user):
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return wrapper
    return decorator


customer_only = role_required(lambda u: u.is_customer)
entrepreneur_only = role_required(lambda u: u.is_entrepreneur)
admin_only = role_required(lambda u: u.is_platform_admin)


def _money(value):
    try:
        return Decimal(value) if value else None
    except InvalidOperation:
        return None


def _can_review(user, profile):
    return (ServiceRequest.objects.filter(customer=user, service__entrepreneur=profile,
                                          status=ServiceRequest.Status.COMPLETED).exists()
            or Order.objects.filter(customer=user, product__entrepreneur=profile,
                                    status=Order.Status.COMPLETED).exists())


# ---------- public pages ----------
def home(request):
    categories = Category.objects.annotate(
        n=Count('entrepreneurprofile', filter=Q(entrepreneurprofile__is_verified=True)))
    featured = (EntrepreneurProfile.objects.filter(is_verified=True, is_available=True)
                .select_related('category').order_by('-created_at')[:6])
    return render(request, 'marketplace/home.html', {'categories': categories, 'featured': featured})


def browse(request):
    g = request.GET
    qs = EntrepreneurProfile.objects.filter(is_verified=True).select_related('category')
    if g.get('category', '').isdigit():
        qs = qs.filter(category_id=g['category'])
    q = g.get('q', '').strip()
    if q:
        qs = qs.filter(Q(business_name__icontains=q) | Q(bio__icontains=q)
                       | Q(services__title__icontains=q) | Q(products__name__icontains=q)).distinct()
    location = g.get('location', '').strip()
    if location:
        qs = qs.filter(location__icontains=location)
    lo, hi = _money(g.get('min')), _money(g.get('max'))
    if lo is not None or hi is not None:
        svc, prod = Q(services__is_active=True), Q(products__is_active=True)
        if lo is not None:
            svc &= Q(services__price__gte=lo)
            prod &= Q(products__price__gte=lo)
        if hi is not None:
            svc &= Q(services__price__lte=hi)
            prod &= Q(products__price__lte=hi)
        qs = qs.filter(svc | prod).distinct()
    return render(request, 'marketplace/browse.html', {
        'results': qs.order_by('-is_available', 'business_name'),
        'categories': Category.objects.all(), 'g': g,
    })


def entrepreneur_detail(request, pk):
    p = get_object_or_404(EntrepreneurProfile.objects.select_related('category', 'user'), pk=pk)
    user = request.user
    is_owner = user.is_authenticated and user.pk == p.user_id
    if not p.is_verified and not (is_owner or (user.is_authenticated and user.is_platform_admin)):
        raise Http404
    reviews = list(p.reviews.select_related('customer')[:20])
    is_customer = user.is_authenticated and user.is_customer
    return render(request, 'marketplace/entrepreneur_detail.html', {
        'p': p, 'reviews': reviews, 'review_count': p.reviews.count(),
        'services': p.services.filter(is_active=True),
        'products': p.products.filter(is_active=True),
        'can_order': is_customer and p.is_verified and p.is_available,
        'can_review': is_customer and _can_review(user, p),
        'is_customer': is_customer, 'is_owner': is_owner,
        'review_form': ReviewForm(),
    })


# ---------- customer actions ----------
@customer_only
@require_POST
def request_service(request, pk):
    service = get_object_or_404(Service, pk=pk, is_active=True)
    profile = service.entrepreneur
    if not profile.is_verified:
        raise Http404
    if not profile.is_available:
        messages.error(request, f'{profile.business_name} is not taking requests right now.')
    else:
        form = ServiceRequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.customer, req.service = request.user, service
            req.save()
            messages.success(request, 'Request sent. You will see the answer under My requests and orders.')
        else:
            messages.error(request, 'Check the date you entered and try again.')
    return redirect('entrepreneur_detail', pk=profile.pk)


@customer_only
@require_POST
@transaction.atomic
def buy_product(request, pk):
    product = get_object_or_404(Product.objects.select_for_update(), pk=pk, is_active=True)
    profile = product.entrepreneur
    if not profile.is_verified:
        raise Http404
    form = OrderForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Enter a quantity of 1 or more.')
    else:
        qty = form.cleaned_data['quantity']
        if qty > product.stock:
            messages.error(request, f'Only {product.stock} of {product.name} left in stock.')
        else:
            Order.objects.create(customer=request.user, product=product, quantity=qty,
                                 total_price=product.price * qty)
            product.stock -= qty
            product.save(update_fields=['stock'])
            messages.success(request, 'Order placed. The seller will confirm it soon.')
    return redirect('entrepreneur_detail', pk=profile.pk)


@customer_only
@require_POST
def add_review(request, pk):
    profile = get_object_or_404(EntrepreneurProfile, pk=pk, is_verified=True)
    if not _can_review(request.user, profile):
        messages.error(request, 'You can leave a review once a request or order with this business is completed.')
    else:
        form = ReviewForm(request.POST)
        if form.is_valid():
            Review.objects.update_or_create(customer=request.user, entrepreneur=profile,
                                            defaults=form.cleaned_data)
            messages.success(request, 'Thanks for your review.')
    return redirect('entrepreneur_detail', pk=pk)


@customer_only
def file_complaint(request, pk):
    profile = get_object_or_404(EntrepreneurProfile, pk=pk)
    form = ComplaintForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        c = form.save(commit=False)
        c.customer, c.entrepreneur = request.user, profile
        c.save()
        messages.success(request, 'Complaint sent to the HunarHub team.')
        return redirect('customer_dashboard')
    return render(request, 'form_page.html', {
        'form': form, 'title': f'Report a problem with {profile.business_name}',
        'intro': 'Tell us what happened. An admin will review it.', 'submit': 'Send complaint',
        'back': reverse('customer_dashboard')})


@customer_only
def customer_dashboard(request):
    return render(request, 'marketplace/customer_dashboard.html', {
        'requests': request.user.service_requests.select_related('service__entrepreneur'),
        'orders': request.user.orders.select_related('product__entrepreneur'),
    })


# ---------- entrepreneur area ----------
def _profile_or_none(user):
    return getattr(user, 'entrepreneur_profile', None)


@entrepreneur_only
def entrepreneur_dashboard(request):
    p = _profile_or_none(request.user)
    if p is None:
        messages.info(request, 'Create your business profile to start selling.')
        return redirect('profile_edit')
    S, O = ServiceRequest.Status, Order.Status
    reqs = ServiceRequest.objects.filter(service__entrepreneur=p)
    orders = Order.objects.filter(product__entrepreneur=p)

    def total(qs, field, status):
        return qs.filter(status=status).aggregate(t=Sum(field))['t'] or 0

    earned = total(reqs, 'service__price', S.COMPLETED) + total(orders, 'total_price', O.COMPLETED)
    in_progress = total(reqs, 'service__price', S.ACCEPTED) + total(orders, 'total_price', O.CONFIRMED)
    return render(request, 'marketplace/entrepreneur_dashboard.html', {
        'p': p, 'earned': earned, 'in_progress': in_progress,
        'pending_count': reqs.filter(status=S.PENDING).count() + orders.filter(status=O.PLACED).count(),
        'requests': reqs.select_related('service', 'customer')[:30],
        'orders': orders.select_related('product', 'customer')[:30],
        'services': p.services.filter(is_active=True), 'products': p.products.filter(is_active=True),
    })


@entrepreneur_only
def profile_edit(request):
    p = _profile_or_none(request.user)
    form = ProfileForm(request.POST or None, request.FILES or None, instance=p)
    if request.method == 'POST' and form.is_valid():
        prof = form.save(commit=False)
        prof.user = request.user
        prof.save()
        messages.success(request, 'Profile saved.' if p else
                         'Profile created. It will appear on HunarHub once an admin approves it.')
        return redirect('entrepreneur_dashboard')
    return render(request, 'form_page.html', {
        'form': form, 'title': 'Your business profile', 'submit': 'Save profile',
        'back': reverse('entrepreneur_dashboard') if p else None})


def _owned_form(request, form_class, model, pk, label):
    profile = _profile_or_none(request.user)
    if profile is None:
        return redirect('profile_edit')
    obj = get_object_or_404(model, pk=pk, entrepreneur=profile) if pk else None
    form = form_class(request.POST or None, request.FILES or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        item = form.save(commit=False)
        item.entrepreneur = profile
        item.save()
        messages.success(request, f'{label.capitalize()} saved.')
        return redirect('entrepreneur_dashboard')
    return render(request, 'form_page.html', {
        'form': form, 'title': f'{"Edit" if obj else "Add"} {label}', 'submit': f'Save {label}',
        'back': reverse('entrepreneur_dashboard')})


@entrepreneur_only
def service_form(request, pk=None):
    return _owned_form(request, ServiceForm, Service, pk, 'service')


@entrepreneur_only
def product_form(request, pk=None):
    return _owned_form(request, ProductForm, Product, pk, 'product')


@entrepreneur_only
@require_POST
def item_remove(request, kind, pk):
    model = {'services': Service, 'products': Product}.get(kind)
    if model is None:
        raise Http404
    item = get_object_or_404(model, pk=pk, entrepreneur=_profile_or_none(request.user))
    item.is_active = False
    item.save(update_fields=['is_active'])
    messages.success(request, 'Removed from your listings.')
    return redirect('entrepreneur_dashboard')


@entrepreneur_only
@require_POST
def toggle_availability(request):
    p = _profile_or_none(request.user)
    if p:
        p.is_available = not p.is_available
        p.save(update_fields=['is_available'])
        messages.success(request, 'You are now taking requests.' if p.is_available
                         else 'You are paused. Customers cannot send new requests.')
    return redirect('entrepreneur_dashboard')


@login_required
@require_POST
def request_action(request, pk, action):
    r = get_object_or_404(ServiceRequest.objects.select_related('service__entrepreneur'), pk=pk)
    S = ServiceRequest.Status
    seller = r.service.entrepreneur.user_id == request.user.id
    buyer = r.customer_id == request.user.id
    rules = {
        'accept': ({S.PENDING}, S.ACCEPTED, seller),
        'reject': ({S.PENDING}, S.REJECTED, seller),
        'complete': ({S.ACCEPTED}, S.COMPLETED, seller),
        'cancel': ({S.PENDING}, S.CANCELLED, buyer),
    }
    rule = rules.get(action)
    if not rule or not rule[2] or r.status not in rule[0]:
        raise PermissionDenied
    r.status = rule[1]
    r.save(update_fields=['status'])
    return redirect('dashboard')


@login_required
@require_POST
@transaction.atomic
def order_action(request, pk, action):
    o = get_object_or_404(Order.objects.select_related('product__entrepreneur'), pk=pk)
    S = Order.Status
    seller = o.product.entrepreneur.user_id == request.user.id
    buyer = o.customer_id == request.user.id
    rules = {
        'confirm': ({S.PLACED}, S.CONFIRMED, seller),
        'complete': ({S.CONFIRMED}, S.COMPLETED, seller),
        'cancel': ({S.PLACED, S.CONFIRMED} if seller else {S.PLACED}, S.CANCELLED, seller or buyer),
    }
    rule = rules.get(action)
    if not rule or not rule[2] or o.status not in rule[0]:
        raise PermissionDenied
    if rule[1] == S.CANCELLED:
        Product.objects.filter(pk=o.product_id).update(stock=F('stock') + o.quantity)
    o.status = rule[1]
    o.save(update_fields=['status'])
    return redirect('dashboard')


# ---------- admin dashboard ----------
@admin_only
def admin_dashboard(request):
    since = timezone.now() - timedelta(days=30)
    S, O = ServiceRequest.Status, Order.Status
    total_requests = ServiceRequest.objects.count()
    converted = ServiceRequest.objects.filter(status__in=[S.ACCEPTED, S.COMPLETED]).count()
    verified = EntrepreneurProfile.objects.filter(is_verified=True).count()
    sales = Order.objects.filter(status__in=[O.CONFIRMED, O.COMPLETED]).aggregate(
        units=Sum('quantity'), value=Sum('total_price'))
    done_orders = Order.objects.filter(status=O.COMPLETED).aggregate(t=Sum('total_price'))['t'] or 0
    done_services = ServiceRequest.objects.filter(status=S.COMPLETED).aggregate(
        t=Sum('service__price'))['t'] or 0
    stats = {
        'entrepreneurs': verified,
        'active_users': User.objects.filter(Q(orders__created_at__gte=since)
                                            | Q(service_requests__created_at__gte=since)).distinct().count(),
        'conversion': round(100 * converted / total_requests) if total_requests else 0,
        'total_requests': total_requests,
        'units': sales['units'] or 0, 'sales_value': sales['value'] or 0,
        'avg_earnings': round((done_orders + done_services) / verified) if verified else 0,
        'avg_rating': Review.objects.aggregate(a=Avg('rating'))['a'],
    }
    return render(request, 'marketplace/admin_dashboard.html', {
        'stats': stats,
        'pending': EntrepreneurProfile.objects.filter(is_verified=False).select_related('user', 'category'),
        'approved': EntrepreneurProfile.objects.filter(is_verified=True).select_related('category')[:50],
        'complaints': Complaint.objects.filter(status=Complaint.Status.OPEN)
                      .select_related('customer', 'entrepreneur'),
        'recent_requests': ServiceRequest.objects.select_related('service__entrepreneur', 'customer')[:10],
        'recent_orders': Order.objects.select_related('product__entrepreneur', 'customer')[:10],
        'categories': Category.objects.all(),
    })


@admin_only
@require_POST
def admin_verify(request, pk, action):
    if action not in ('approve', 'revoke'):
        raise Http404
    p = get_object_or_404(EntrepreneurProfile, pk=pk)
    p.is_verified = action == 'approve'
    p.save(update_fields=['is_verified'])
    messages.success(request, f'{p.business_name} {"approved" if p.is_verified else "unapproved"}.')
    return redirect('admin_dashboard')


@admin_only
@require_POST
def category_add(request):
    name = request.POST.get('name', '').strip()
    if name:
        _, created = Category.objects.get_or_create(name=name)
        messages.success(request, f'Category "{name}" added.' if created else 'That category already exists.')
    return redirect('admin_dashboard')


@admin_only
@require_POST
def category_delete(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    try:
        cat.delete()
        messages.success(request, f'Category "{cat.name}" deleted.')
    except ProtectedError:
        messages.error(request, f'"{cat.name}" still has entrepreneurs, so it cannot be deleted.')
    return redirect('admin_dashboard')


@admin_only
@require_POST
def complaint_resolve(request, pk):
    c = get_object_or_404(Complaint, pk=pk)
    c.status = Complaint.Status.RESOLVED
    c.admin_note = request.POST.get('admin_note', '').strip()
    c.save(update_fields=['status', 'admin_note'])
    messages.success(request, 'Complaint marked as resolved.')
    return redirect('admin_dashboard')
