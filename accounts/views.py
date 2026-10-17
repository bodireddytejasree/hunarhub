from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import RegisterForm


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('dashboard')
    return render(request, 'form_page.html', {
        'form': form, 'title': 'Create your account', 'submit': 'Create account',
        'alt_text': 'Already have an account?', 'alt_link': 'Log in', 'alt_url': '/login/',
    })


@login_required
def dashboard(request):
    user = request.user
    if user.is_platform_admin:
        return redirect('admin_dashboard')
    if user.is_entrepreneur:
        return redirect('entrepreneur_dashboard')
    return redirect('customer_dashboard')
