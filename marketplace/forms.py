from django import forms

from .models import Complaint, EntrepreneurProfile, Order, Product, Review, Service, ServiceRequest


class ProfileForm(forms.ModelForm):
    class Meta:
        model = EntrepreneurProfile
        fields = ['category', 'business_name', 'bio', 'experience_years', 'location', 'photo']


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['title', 'description', 'price']


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock', 'image']


class ServiceRequestForm(forms.ModelForm):
    preferred_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = ServiceRequest
        fields = ['message', 'preferred_date']


class OrderForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, initial=1)


class ReviewForm(forms.ModelForm):
    rating = forms.TypedChoiceField(
        choices=[(i, f'{i} star{"s" if i > 1 else ""}') for i in range(5, 0, -1)], coerce=int)

    class Meta:
        model = Review
        fields = ['rating', 'comment']


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['subject', 'details']
