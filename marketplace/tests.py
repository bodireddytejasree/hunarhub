from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Category, EntrepreneurProfile, Order, Product, Review, Service, ServiceRequest

User = get_user_model()


class FlowTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name='Tailor')
        self.seller = User.objects.create_user('seller', password='x', role='entrepreneur')
        self.p = EntrepreneurProfile.objects.create(
            user=self.seller, category=cat, business_name='S Tailors', location='Tirupati', is_verified=True)
        self.svc = Service.objects.create(entrepreneur=self.p, title='Blouse', price=400)
        self.prod = Product.objects.create(entrepreneur=self.p, name='Bag', price=100, stock=3)
        self.buyer = User.objects.create_user('buyer', password='x')

    def test_unverified_profile_is_hidden(self):
        self.p.is_verified = False
        self.p.save()
        self.assertNotContains(self.client.get(reverse('browse')), 'S Tailors')
        self.assertEqual(self.client.get(reverse('entrepreneur_detail', args=[self.p.pk])).status_code, 404)

    def test_price_filter(self):
        url = reverse('browse')
        self.assertContains(self.client.get(url, {'min': 50, 'max': 450}), 'S Tailors')
        self.assertNotContains(self.client.get(url, {'min': 1000}), 'S Tailors')

    def test_request_accept_complete_then_review(self):
        self.client.login(username='buyer', password='x')
        self.client.post(reverse('request_service', args=[self.svc.pk]), {'message': 'Please'})
        req = ServiceRequest.objects.get()
        self.client.post(reverse('add_review', args=[self.p.pk]), {'rating': 5, 'comment': 'Great'})
        self.assertEqual(Review.objects.count(), 0)  # not completed yet
        self.client.login(username='seller', password='x')
        self.client.post(reverse('request_action', args=[req.pk, 'accept']))
        self.client.post(reverse('request_action', args=[req.pk, 'complete']))
        self.client.login(username='buyer', password='x')
        self.client.post(reverse('add_review', args=[self.p.pk]), {'rating': 5, 'comment': 'Great'})
        self.assertEqual(Review.objects.get().rating, 5)

    def test_order_stock_and_oversell(self):
        self.client.login(username='buyer', password='x')
        self.client.post(reverse('buy_product', args=[self.prod.pk]), {'quantity': 2})
        self.client.post(reverse('buy_product', args=[self.prod.pk]), {'quantity': 5})
        self.prod.refresh_from_db()
        self.assertEqual(self.prod.stock, 1)
        self.assertEqual(Order.objects.count(), 1)
        self.client.post(reverse('order_action', args=[Order.objects.get().pk, 'cancel']))
        self.prod.refresh_from_db()
        self.assertEqual(self.prod.stock, 3)

    def test_role_protection(self):
        self.client.login(username='buyer', password='x')
        self.assertEqual(self.client.get(reverse('entrepreneur_dashboard')).status_code, 403)
        self.assertEqual(self.client.get(reverse('admin_dashboard')).status_code, 403)
        order = Order.objects.create(customer=self.buyer, product=self.prod, quantity=1, total_price=100)
        self.assertEqual(self.client.post(reverse('order_action', args=[order.pk, 'confirm'])).status_code, 403)

    def test_admin_can_approve(self):
        self.p.is_verified = False
        self.p.save()
        User.objects.create_superuser('boss', 'b@x.com', 'x')
        self.client.login(username='boss', password='x')
        self.client.post(reverse('admin_verify', args=[self.p.pk, 'approve']))
        self.p.refresh_from_db()
        self.assertTrue(self.p.is_verified)
        self.assertEqual(self.client.get(reverse('admin_dashboard')).status_code, 200)
