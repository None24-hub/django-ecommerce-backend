import json

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from basket.models import Basket, BasketItem
from catalog.models import Category, Product, ProductImage
from orders.models import Order, OrderItem

User = get_user_model()


class OrdersApiTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(title="Computers")
        self.product_1 = Product.objects.create(
            category=self.category,
            title="RTX",
            description="GPU",
            price=1000,
            count=10,
            free_delivery=True,
            rating=4.5,
        )
        self.product_2 = Product.objects.create(
            category=self.category,
            title="CPU",
            description="CPU",
            price=500,
            count=5,
            free_delivery=False,
            rating=4.0,
        )
        ProductImage.objects.create(
            product=self.product_1,
            src="/static/frontend/assets/img/content/home/card.jpg",
            alt="RTX",
            sort_order=0,
        )
        ProductImage.objects.create(
            product=self.product_2,
            src="/static/frontend/assets/img/content/home/slider.png",
            alt="CPU",
            sort_order=0,
        )

    def test_create_order_from_anonymous_session_basket(self):
        session = self.client.session
        session["basket_items"] = {str(self.product_1.id): 2, str(self.product_2.id): 1}
        session.save()

        response = self.client.post("/api/orders", data=[], format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("orderId", response.data)
        order = Order.objects.get(id=response.data["orderId"])
        self.assertIsNone(order.user_id)
        self.assertEqual(OrderItem.objects.filter(order=order).count(), 2)
        session = self.client.session
        self.assertEqual(session.get("basket_items"), {})
        self.assertIn(order.id, session.get("order_ids", []))

    def test_create_order_from_authenticated_db_basket(self):
        user = User.objects.create_user(username="order_user", password="12345678")
        basket = Basket.objects.create(user=user)
        BasketItem.objects.create(basket=basket, product=self.product_1, count=3)
        self.client.login(username="order_user", password="12345678")

        response = self.client.post("/api/orders", data=[], format="json")
        self.assertEqual(response.status_code, 200)
        order = Order.objects.get(id=response.data["orderId"])
        self.assertEqual(order.user_id, user.id)
        self.assertEqual(OrderItem.objects.filter(order=order).count(), 1)
        self.assertFalse(BasketItem.objects.filter(basket=basket).exists())

    def test_orders_list_and_detail_basic(self):
        user = User.objects.create_user(username="history_user", password="12345678")
        order = Order.objects.create(
            user=user,
            full_name="Test User",
            email="test@example.com",
            phone="+70000000000",
            delivery_type="free",
            payment_type="online",
            total_cost=1500,
            status="accepted",
            city="Moscow",
            address="Red square 1",
        )
        OrderItem.objects.create(
            order=order,
            product=self.product_1,
            count=1,
            unit_price=self.product_1.price,
        )
        self.client.login(username="history_user", password="12345678")

        list_response = self.client.get("/api/orders")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(list_response.data[0]["id"], order.id)

        detail_response = self.client.get(f"/api/orders/{order.id}")
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.data["id"], order.id)
        self.assertEqual(len(detail_response.data["products"]), 1)

        confirm_response = self.client.post(
            f"/api/orders/{order.id}",
            data=json.dumps(
                {
                    "fullName": "Confirmed User",
                    "email": "confirmed@example.com",
                    "phone": "+79998887766",
                    "deliveryType": "express",
                    "paymentType": "online",
                    "city": "Kazan",
                    "address": "Lenina 1",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(confirm_response.status_code, 200)
        self.assertEqual(confirm_response.data["orderId"], order.id)
