from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from orders.models import Order
from payments.models import Payment

User = get_user_model()


class PaymentsApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="payment_user",
            password="12345678",
        )
        self.order = Order.objects.create(
            user=self.user,
            full_name="Payment User",
            email="pay@example.com",
            phone="+70000000000",
            delivery_type="free",
            payment_type="online",
            total_cost=1000,
            status="accepted",
            city="Moscow",
            address="Lenina 1",
        )

    def test_successful_payment(self):
        self.client.login(username="payment_user", password="12345678")

        response = self.client.post(
            f"/api/payment/{self.order.id}",
            data={
                "number": "4242424242424242",
                "name": "Payment User",
                "month": "12",
                "year": "30",
                "code": "123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "paid")
        payment = Payment.objects.get(order=self.order)
        self.assertEqual(payment.status, Payment.STATUS_SUCCEEDED)
        self.assertEqual(payment.card_number_masked, "**** **** **** 4242")

    def test_payment_validation_error(self):
        self.client.login(username="payment_user", password="12345678")

        response = self.client.post(
            f"/api/payment/{self.order.id}",
            data={
                "number": "123",
                "name": "",
                "month": "99",
                "year": "2",
                "code": "1",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "payment_failed")
        payment = Payment.objects.get(order=self.order)
        self.assertEqual(payment.status, Payment.STATUS_FAILED)
        self.assertTrue(payment.error_message)

    def test_order_detail_contains_payment_error_after_failed_payment(self):
        self.client.login(username="payment_user", password="12345678")

        self.client.post(
            f"/api/payment/{self.order.id}",
            data={
                "number": "1111",
                "name": "Payment User",
                "month": "12",
                "year": "30",
                "code": "12",
            },
            format="json",
        )

        detail_response = self.client.get(f"/api/order/{self.order.id}")
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.data["status"], "payment_failed")
        self.assertEqual(
            detail_response.data["paymentError"],
            "Invalid payment data.",
        )
