from decimal import Decimal

from rest_framework import serializers

from catalog.serializers import ImageSerializer
from orders.models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="product_id")
    category = serializers.IntegerField(source="product.category_id")
    title = serializers.CharField(source="product.title")
    description = serializers.CharField(source="product.description")
    freeDelivery = serializers.BooleanField(source="product.free_delivery")
    images = ImageSerializer(source="product.images", many=True, read_only=True)
    reviews = serializers.IntegerField(source="product.reviews_count", read_only=True)
    rating = serializers.FloatField(source="product.rating_value", read_only=True)
    price = serializers.SerializerMethodField()
    date = serializers.DateTimeField(
        source="product.created_at",
        format="%Y-%m-%d %H:%M:%S",
    )

    class Meta:
        model = OrderItem
        fields = (
            "id",
            "category",
            "price",
            "count",
            "date",
            "title",
            "description",
            "freeDelivery",
            "images",
            "reviews",
            "rating",
        )

    def get_price(self, obj):
        return obj.unit_price * Decimal(obj.count)


class OrderSerializer(serializers.ModelSerializer):
    createdAt = serializers.DateTimeField(source="created_at", format="%Y-%m-%d %H:%M")
    fullName = serializers.CharField(source="full_name")
    deliveryType = serializers.CharField(source="delivery_type")
    paymentType = serializers.CharField(source="payment_type")
    totalCost = serializers.DecimalField(source="total_cost", max_digits=12, decimal_places=2)
    paymentError = serializers.SerializerMethodField()
    products = OrderItemSerializer(source="items", many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "createdAt",
            "fullName",
            "email",
            "phone",
            "deliveryType",
            "paymentType",
            "totalCost",
            "status",
            "paymentError",
            "city",
            "address",
            "products",
        )

    def get_paymentError(self, obj):
        payment = getattr(obj, "payment", None)
        if payment is None:
            return None
        if payment.status != "failed":
            return None
        return payment.error_message or "Payment was declined."
