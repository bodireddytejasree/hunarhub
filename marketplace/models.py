from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg

PRICE = dict(max_digits=9, decimal_places=2, validators=[MinValueValidator(Decimal('0'))])


class Category(models.Model):
    name = models.CharField(max_length=60, unique=True)

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class EntrepreneurProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='entrepreneur_profile')
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    business_name = models.CharField(max_length=120)
    bio = models.TextField('About you and your work', blank=True)
    experience_years = models.PositiveIntegerField('Years of experience', default=0)
    location = models.CharField('Town or area', max_length=120)
    photo = models.ImageField(upload_to='profiles/', blank=True)
    is_verified = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.business_name

    @property
    def avg_rating(self):
        return self.reviews.aggregate(a=Avg('rating'))['a']


class Service(models.Model):
    entrepreneur = models.ForeignKey(EntrepreneurProfile, on_delete=models.CASCADE, related_name='services')
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    price = models.DecimalField('Price (₹)', **PRICE)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Product(models.Model):
    entrepreneur = models.ForeignKey(EntrepreneurProfile, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    price = models.DecimalField('Price (₹)', **PRICE)
    image = models.ImageField(upload_to='products/', blank=True)
    stock = models.PositiveIntegerField('Number in stock', default=1)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class ServiceRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='service_requests')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='requests')
    message = models.TextField(blank=True)
    preferred_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class Order(models.Model):
    class Status(models.TextChoices):
        PLACED = 'placed', 'Placed'
        CONFIRMED = 'confirmed', 'Confirmed'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='orders')
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=11, decimal_places=2)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PLACED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class Review(models.Model):
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    entrepreneur = models.ForeignKey(EntrepreneurProfile, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [models.UniqueConstraint(fields=['customer', 'entrepreneur'], name='one_review_per_customer')]


class Complaint(models.Model):
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        RESOLVED = 'resolved', 'Resolved'

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='complaints')
    entrepreneur = models.ForeignKey(EntrepreneurProfile, on_delete=models.CASCADE, related_name='complaints')
    subject = models.CharField(max_length=140)
    details = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    admin_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
