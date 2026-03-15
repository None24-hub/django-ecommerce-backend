import json

from rest_framework.test import APITestCase

from catalog.models import Category, Product, ProductImage


class BasketSessionApiTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(title="Components")

        self.product_1 = Product.objects.create(
            category=self.category,
            title="GPU One",
            description="GPU",
            price=1000,
            count=99,
            free_delivery=True,
            rating=4.5,
        )
        self.product_2 = Product.objects.create(
            category=self.category,
            title="CPU Two",
            description="CPU",
            price=500,
            count=99,
            free_delivery=False,
            rating=4.0,
        )

        ProductImage.objects.create(
            product=self.product_1,
            src="/static/frontend/assets/img/content/home/card.jpg",
            alt="GPU One",
            sort_order=0,
        )
        ProductImage.objects.create(
            product=self.product_2,
            src="/static/frontend/assets/img/content/home/slider.png",
            alt="CPU Two",
            sort_order=0,
        )

    @staticmethod
    def _get_item(response_data, product_id):
        return next(item for item in response_data if item["id"] == product_id)

    def test_anonymous_basket_add_update_remove_and_clear(self):
        response = self.client.get("/api/basket")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

        response = self.client.post(
            "/api/basket",
            data={"id": self.product_1.id, "count": 2},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._get_item(response.data, self.product_1.id)["count"], 2)
        self.assertEqual(self.client.session["basket_items"], {str(self.product_1.id): 2})

        response = self.client.post(
            "/api/basket",
            data={"id": self.product_1.id, "count": 3},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._get_item(response.data, self.product_1.id)["count"], 5)

        response = self.client.post(
            "/api/basket",
            data={"id": self.product_2.id, "count": 1},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(self._get_item(response.data, self.product_2.id)["count"], 1)

        response = self.client.delete(
            "/api/basket",
            data=json.dumps({"id": self.product_1.id, "count": 2}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._get_item(response.data, self.product_1.id)["count"], 3)

        response = self.client.delete(
            "/api/basket",
            data=json.dumps({"id": self.product_1.id, "count": 10}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.product_2.id)

        response = self.client.delete(
            "/api/basket",
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])
        self.assertEqual(self.client.session["basket_items"], {})

    def test_add_invalid_product_returns_400(self):
        response = self.client.post(
            "/api/basket",
            data={"id": 999999, "count": 1},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
