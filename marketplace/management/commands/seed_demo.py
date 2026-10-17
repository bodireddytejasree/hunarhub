from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from marketplace.models import Category, EntrepreneurProfile, Product, Service

User = get_user_model()

DEMO = [
    ('ramesh', 'Ramesh Footwear Repair', 'Cobbler', 'Kakinada', 12,
     'Shoe and bag repair, polishing and custom leather sandals.',
     [('Shoe sole repair', 150), ('Leather polish', 60)], [('Handmade leather sandals', 650, 10)]),
    ('lakshmi', 'Lakshmi Clay Works', 'Potter (Kumhar)', 'Rajahmundry', 20,
     'Terracotta pots, diyas and kitchenware shaped on the wheel.',
     [('Custom clay order', 500)], [('Terracotta water pot', 350, 15), ('Clay diya set of 12', 120, 40)]),
    ('sita', 'Sita Tailoring', 'Tailor', 'Tirupati', 9,
     'Blouses, kurtas and alterations stitched to measure.',
     [('Blouse stitching', 400), ('Alterations', 120)], [('Cotton tote bag', 180, 25)]),
    ('venkat', 'Venkat Wooden Toys', 'Artisan', 'Vijayawada', 25,
     'Hand-painted wooden toys in the Kondapalli tradition.',
     [], [('Wooden toy set', 900, 8)]),
    ('anjali', 'Anjali Home Pickles', 'Small vendor', 'Visakhapatnam', 6,
     'Small-batch pickles and podis made at home.',
     [], [('Mango pickle 500g', 220, 30), ('Karam podi 250g', 140, 30)]),
]


class Command(BaseCommand):
    help = 'Load demo categories, verified entrepreneurs, a customer and an admin.'

    def handle(self, *args, **options):
        cats = {n: Category.objects.get_or_create(name=n)[0]
                for n in ['Cobbler', 'Potter (Kumhar)', 'Tailor', 'Artisan', 'Small vendor']}
        for username, biz, cat, loc, exp, bio, services, products in DEMO:
            user, created = User.objects.get_or_create(username=username, defaults={'role': 'entrepreneur'})
            if created:
                user.set_password('demo12345')
                user.save()
            profile, _ = EntrepreneurProfile.objects.get_or_create(user=user, defaults=dict(
                category=cats[cat], business_name=biz, bio=bio, experience_years=exp,
                location=loc, is_verified=True))
            for title, price in services:
                Service.objects.get_or_create(entrepreneur=profile, title=title, defaults={'price': price})
            for name, price, stock in products:
                Product.objects.get_or_create(entrepreneur=profile, name=name,
                                              defaults={'price': price, 'stock': stock})
        if not User.objects.filter(username='customer').exists():
            User.objects.create_user('customer', 'customer@example.com', 'demo12345')
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin12345')
        self.stdout.write(self.style.SUCCESS(
            'Demo data ready. Logins: customer / demo12345, ramesh / demo12345, admin / admin12345'))
