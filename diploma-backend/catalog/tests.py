from django.utils import timezone
from rest_framework.test import APITestCase

from catalog.models import Category, Product, ProductImage, Review


class CatalogApiTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(title="Computers")

        self.first = Product.objects.create(
            category=self.category,
            title="Product A",
            description="A",
            full_description="A full",
            price=1000,
            count=3,
            free_delivery=True,
            rating=3.5,
            is_popular=True,
            is_limited=True,
            is_banner=True,
            sale_price=900,
            sale_date_from=timezone.now().date() - timezone.timedelta(days=3),
            sale_date_to=timezone.now().date() + timezone.timedelta(days=7),
            created_at=timezone.now() - timezone.timedelta(days=2),
        )
        self.second = Product.objects.create(
            category=self.category,
            title="Product B",
            description="B",
            full_description="B full",
            price=500,
            count=1,
            free_delivery=False,
            rating=4.5,
            is_popular=True,
            created_at=timezone.now() - timezone.timedelta(days=1),
        )
        self.third = Product.objects.create(
            category=self.category,
            title="Product C",
            description="C",
            full_description="C full",
            price=1500,
            count=0,
            free_delivery=True,
            rating=2.0,
            is_limited=True,
            is_banner=True,
            sale_price=1200,
            sale_date_from=timezone.now().date() - timezone.timedelta(days=1),
            sale_date_to=timezone.now().date() + timezone.timedelta(days=10),
            created_at=timezone.now(),
        )

        ProductImage.objects.create(product=self.first, src="/static/1.png", alt="1")
        ProductImage.objects.create(product=self.second, src="/static/2.png", alt="2")
        ProductImage.objects.create(product=self.third, src="/static/3.png", alt="3")

        Review.objects.create(
            product=self.first,
            author="Ann",
            email="ann@example.com",
            text="good",
            rate=5,
        )
        Review.objects.create(
            product=self.first,
            author="Bob",
            email="bob@example.com",
            text="ok",
            rate=4,
        )
        Review.objects.create(
            product=self.second,
            author="Cat",
            email="cat@example.com",
            text="normal",
            rate=3,
        )

    def test_catalog_filtering(self):
        response = self.client.get(
            "/api/catalog",
            {
                "filter[minPrice]": 900,
                "filter[maxPrice]": 1600,
                "filter[freeDelivery]": "true",
                "filter[available]": "true",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["items"][0]["id"], self.first.id)

    def test_catalog_sorting_by_price(self):
        response = self.client.get(
            "/api/catalog",
            {
                "sort": "price",
                "sortType": "inc",
            },
        )
        self.assertEqual(response.status_code, 200)
        product_ids = [item["id"] for item in response.data["items"]]
        self.assertEqual(product_ids, [self.second.id, self.first.id, self.third.id])

    def test_popular_products_showcase(self):
        response = self.client.get("/api/products/popular")
        self.assertEqual(response.status_code, 200)
        product_ids = [item["id"] for item in response.data]
        self.assertEqual(product_ids, [self.first.id, self.second.id])

    def test_limited_products_showcase(self):
        response = self.client.get("/api/products/limited")
        self.assertEqual(response.status_code, 200)
        product_ids = [item["id"] for item in response.data]
        self.assertEqual(product_ids, [self.third.id, self.first.id])

    def test_banners_showcase(self):
        response = self.client.get("/api/banners")
        self.assertEqual(response.status_code, 200)
        product_ids = [item["id"] for item in response.data]
        self.assertEqual(product_ids, [self.third.id, self.first.id])

    def test_sales_showcase(self):
        response = self.client.get("/api/sales", {"currentPage": 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data.keys()), {"items", "currentPage", "lastPage"})
        self.assertEqual(response.data["currentPage"], 1)
        sale_ids = [item["id"] for item in response.data["items"]]
        self.assertEqual(sale_ids, [str(self.third.id), str(self.first.id)])
