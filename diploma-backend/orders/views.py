from decimal import Decimal

from django.db.models import Avg, Count, F, FloatField, Prefetch, Q, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from basket.models import BasketItem
from catalog.models import Product, ProductImage
from orders.models import Order, OrderItem
from orders.serializers import OrderSerializer


class OrdersAPIView(APIView):
    anon_orders_session_key = "order_ids"
    anon_basket_session_key = "basket_items"

    def get(self, request):
        orders = self._get_accessible_orders_queryset(request)
        return Response(OrderSerializer(orders, many=True).data)

    def post(self, request):
        basket_map = self._get_current_basket_map(request)
        if not basket_map:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        product_ids = [int(product_id) for product_id in basket_map.keys()]
        products = {
            product.id: product
            for product in Product.objects.filter(id__in=product_ids).only("id", "price")
        }
        if not products:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            status="created",
        )

        order_items = []
        total_cost = Decimal("0")
        for product_id, count in basket_map.items():
            product = products.get(int(product_id))
            if product is None:
                continue
            unit_price = product.price
            total_cost += unit_price * Decimal(count)
            order_items.append(
                OrderItem(
                    order=order,
                    product=product,
                    count=count,
                    unit_price=unit_price,
                )
            )

        if not order_items:
            order.delete()
            return Response(status=status.HTTP_400_BAD_REQUEST)

        OrderItem.objects.bulk_create(order_items)
        order.total_cost = total_cost
        order.save(update_fields=["total_cost"])

        self._clear_current_basket(request)
        if not request.user.is_authenticated:
            order_ids = request.session.get(self.anon_orders_session_key, [])
            if order.id not in order_ids:
                order_ids.append(order.id)
            request.session[self.anon_orders_session_key] = order_ids
            request.session.modified = True

        return Response({"orderId": order.id}, status=status.HTTP_200_OK)

    def _get_current_basket_map(self, request):
        if request.user.is_authenticated:
            rows = (
                BasketItem.objects.filter(basket__user=request.user)
                .select_related("product")
                .only("product_id", "count")
            )
            return {str(row.product_id): int(row.count) for row in rows if row.count > 0}

        raw = request.session.get(self.anon_basket_session_key, {})
        if not isinstance(raw, dict):
            return {}

        normalized = {}
        for key, value in raw.items():
            try:
                product_id = int(key)
                count = int(value)
            except (TypeError, ValueError):
                continue
            if product_id <= 0 or count <= 0:
                continue
            normalized[str(product_id)] = count
        return normalized

    def _clear_current_basket(self, request):
        if request.user.is_authenticated:
            BasketItem.objects.filter(basket__user=request.user).delete()
            return
        request.session[self.anon_basket_session_key] = {}
        request.session.modified = True

    def _get_accessible_orders_queryset(self, request):
        base_qs = (
            Order.objects.select_related("user")
            .only(
                "id",
                "user_id",
                "full_name",
                "email",
                "phone",
                "delivery_type",
                "payment_type",
                "total_cost",
                "status",
                "city",
                "address",
                "created_at",
            )
            .prefetch_related(
                Prefetch(
                    "items",
                    queryset=(
                        OrderItem.objects.select_related("product", "product__category")
                        .only(
                            "id",
                            "order_id",
                            "product_id",
                            "count",
                            "unit_price",
                            "product__id",
                            "product__category_id",
                            "product__title",
                            "product__description",
                            "product__created_at",
                            "product__free_delivery",
                            "product__rating",
                        )
                        .prefetch_related(
                            Prefetch(
                                "product__images",
                                queryset=ProductImage.objects.only(
                                    "id",
                                    "product_id",
                                    "src",
                                    "alt",
                                    "sort_order",
                                ).order_by("sort_order", "id"),
                            )
                        )
                        .annotate(
                            reviews_count=Count("product__reviews", distinct=True),
                            rating_value=Coalesce(
                                Avg("product__reviews__rate"),
                                F("product__rating"),
                                Value(0.0),
                                output_field=FloatField(),
                            ),
                        )
                    ),
                )
            )
        )

        if request.user.is_authenticated:
            return base_qs.filter(user=request.user)

        order_ids = request.session.get(self.anon_orders_session_key, [])
        if not isinstance(order_ids, list):
            return base_qs.none()
        order_ids = [order_id for order_id in order_ids if isinstance(order_id, int)]
        if not order_ids:
            return base_qs.none()
        return base_qs.filter(id__in=order_ids)


class OrderDetailAPIView(APIView):
    anon_orders_session_key = "order_ids"

    def get(self, request, order_id):
        order = self._get_accessible_order(request, order_id)
        return Response(OrderSerializer(order).data)

    def post(self, request, order_id):
        order = self._get_accessible_order(request, order_id)

        payload = request.data if isinstance(request.data, dict) else {}
        order.full_name = str(payload.get("fullName", order.full_name or "")).strip()
        order.email = str(payload.get("email", order.email or "")).strip()
        order.phone = str(payload.get("phone", order.phone or "")).strip()
        order.delivery_type = str(payload.get("deliveryType", order.delivery_type or "")).strip()
        order.payment_type = str(payload.get("paymentType", order.payment_type or "")).strip()
        order.city = str(payload.get("city", order.city or "")).strip()
        order.address = str(payload.get("address", order.address or "")).strip()

        if order.status in {"created", "", None}:
            order.status = "accepted"

        order.save(
            update_fields=[
                "full_name",
                "email",
                "phone",
                "delivery_type",
                "payment_type",
                "city",
                "address",
                "status",
                "updated_at",
            ]
        )
        return Response({"orderId": order.id}, status=status.HTTP_200_OK)

    def _get_accessible_order(self, request, order_id):
        allowed_q = Q(id=order_id)
        if request.user.is_authenticated:
            allowed_q &= Q(user=request.user)
        else:
            order_ids = request.session.get(self.anon_orders_session_key, [])
            if not isinstance(order_ids, list):
                order_ids = []
            allowed_q &= Q(id__in=[value for value in order_ids if isinstance(value, int)])

        queryset = (
            Order.objects.select_related("user")
            .only(
                "id",
                "user_id",
                "full_name",
                "email",
                "phone",
                "delivery_type",
                "payment_type",
                "total_cost",
                "status",
                "city",
                "address",
                "created_at",
            )
            .prefetch_related(
                Prefetch(
                    "items",
                    queryset=(
                        OrderItem.objects.select_related("product", "product__category")
                        .only(
                            "id",
                            "order_id",
                            "product_id",
                            "count",
                            "unit_price",
                            "product__id",
                            "product__category_id",
                            "product__title",
                            "product__description",
                            "product__created_at",
                            "product__free_delivery",
                            "product__rating",
                        )
                        .prefetch_related(
                            Prefetch(
                                "product__images",
                                queryset=ProductImage.objects.only(
                                    "id",
                                    "product_id",
                                    "src",
                                    "alt",
                                    "sort_order",
                                ).order_by("sort_order", "id"),
                            )
                        )
                        .annotate(
                            reviews_count=Count("product__reviews", distinct=True),
                            rating_value=Coalesce(
                                Avg("product__reviews__rate"),
                                F("product__rating"),
                                Value(0.0),
                                output_field=FloatField(),
                            ),
                        )
                    ),
                )
            )
        )
        return get_object_or_404(queryset, allowed_q)
