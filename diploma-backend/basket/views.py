import json

from django.db.models import Avg, Count, F, FloatField, Prefetch, Value
from django.db.models.functions import Coalesce
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from basket.serializers import BasketItemSerializer
from catalog.models import Product, ProductImage, Tag


class BasketAPIView(APIView):
    session_key = "basket_items"

    def get(self, request):
        return Response(self._build_response_items(request))

    def post(self, request):
        payload = self._extract_payload(request)
        product_id = self._to_int(payload.get("id"))
        count = self._to_int(payload.get("count"), 1)
        if product_id is None or count is None or count <= 0:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if not Product.objects.filter(id=product_id).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        basket = self._get_basket_session(request)
        key = str(product_id)
        basket[key] = basket.get(key, 0) + count
        self._set_basket_session(request, basket)
        return Response(self._build_response_items(request))

    def delete(self, request):
        payload = self._extract_payload(request)
        basket = self._get_basket_session(request)

        if "id" not in payload:
            self._set_basket_session(request, {})
            return Response([])

        product_id = self._to_int(payload.get("id"))
        if product_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        key = str(product_id)
        current_count = basket.get(key, 0)
        if current_count <= 0:
            return Response(self._build_response_items(request))

        remove_count = self._to_int(payload.get("count"), current_count)
        if remove_count is None or remove_count <= 0:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if remove_count >= current_count:
            basket.pop(key, None)
        else:
            basket[key] = current_count - remove_count
        self._set_basket_session(request, basket)
        return Response(self._build_response_items(request))

    @staticmethod
    def _to_int(value, default=None):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _extract_payload(self, request):
        if isinstance(request.data, dict):
            return request.data
        if isinstance(request.data, str):
            try:
                payload = json.loads(request.data)
                if isinstance(payload, dict):
                    return payload
            except json.JSONDecodeError:
                return {}
        return {}

    def _get_basket_session(self, request):
        raw_basket = request.session.get(self.session_key, {})
        if not isinstance(raw_basket, dict):
            return {}

        normalized = {}
        for key, value in raw_basket.items():
            product_id = self._to_int(key)
            count = self._to_int(value)
            if product_id is None or count is None or count <= 0:
                continue
            normalized[str(product_id)] = count
        return normalized

    def _set_basket_session(self, request, basket):
        request.session[self.session_key] = basket
        request.session.modified = True

    def _build_response_items(self, request):
        basket = self._get_basket_session(request)
        if not basket:
            self._set_basket_session(request, {})
            return []

        product_ids = [int(product_id) for product_id in basket.keys()]
        products_qs = (
            Product.objects.filter(id__in=product_ids)
            .select_related("category")
            .only(
                "id",
                "category_id",
                "price",
                "title",
                "description",
                "created_at",
                "free_delivery",
                "rating",
            )
            .prefetch_related(
                Prefetch(
                    "images",
                    queryset=ProductImage.objects.only(
                        "id",
                        "product_id",
                        "src",
                        "alt",
                        "sort_order",
                    ).order_by("sort_order", "id"),
                ),
                Prefetch("tags", queryset=Tag.objects.only("id", "name")),
            )
            .annotate(
                reviews_count=Count("reviews", distinct=True),
                rating_value=Coalesce(
                    Avg("reviews__rate"),
                    F("rating"),
                    Value(0.0),
                    output_field=FloatField(),
                ),
            )
        )
        products_map = {product.id: product for product in products_qs}

        items = []
        cleaned_basket = {}
        for product_id in product_ids:
            product = products_map.get(product_id)
            if product is None:
                continue
            count = basket[str(product_id)]
            product.basket_count = count
            items.append(product)
            cleaned_basket[str(product_id)] = count

        if cleaned_basket != basket:
            self._set_basket_session(request, cleaned_basket)

        serializer = BasketItemSerializer(items, many=True)
        return serializer.data
