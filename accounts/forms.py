from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class RegisterForm(UserCreationForm):
    role = forms.ChoiceField(
        label='I want to',
        choices=[('customer', 'Find and hire local talent, and buy handmade products'),
                 ('entrepreneur', 'Sell my skills and products')],
        widget=forms.RadioSelect,
        initial='customer',
    )
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'phone', 'role')
