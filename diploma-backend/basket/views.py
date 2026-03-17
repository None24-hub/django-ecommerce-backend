import json

from django.db.models import Avg, Count, F, FloatField, Prefetch, Value
from django.db.models.functions import Coalesce
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from basket.models import Basket, BasketItem
from basket.serializers import BasketItemSerializer
from catalog.models import Product, ProductImage, Tag


class BasketAPIView(APIView):
    session_key = "basket_items"

    def get(self, request):
        self._merge_session_to_db_if_needed(request)
        return Response(self._build_response_items(request))

    def post(self, request):
        payload = self._extract_payload(request)
        product_id = self._to_int(payload.get("id"))
        count = self._to_int(payload.get("count"), 1)
        if product_id is None or count is None or count <= 0:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if not Product.objects.filter(id=product_id).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if request.user.is_authenticated:
            self._merge_session_to_db_if_needed(request)
            basket = self._get_or_create_user_basket(request.user)
            item, created = BasketItem.objects.get_or_create(
                basket=basket,
                product_id=product_id,
                defaults={"count": count},
            )
            if not created:
                item.count += count
                item.save(update_fields=["count", "updated_at"])
        else:
            basket = self._get_basket_session(request)
            key = str(product_id)
            basket[key] = basket.get(key, 0) + count
            self._set_basket_session(request, basket)
        return Response(self._build_response_items(request))

    def delete(self, request):
        payload = self._extract_payload(request)
        self._merge_session_to_db_if_needed(request)

        if "id" not in payload:
            if request.user.is_authenticated:
                BasketItem.objects.filter(basket__user=request.user).delete()
            else:
                self._set_basket_session(request, {})
            return Response([])

        product_id = self._to_int(payload.get("id"))
        if product_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if request.user.is_authenticated:
            item = BasketItem.objects.filter(
                basket__user=request.user,
                product_id=product_id,
            ).first()
            if item is None:
                return Response(self._build_response_items(request))
            remove_count = self._to_int(payload.get("count"), item.count)
            if remove_count is None or remove_count <= 0:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            if remove_count >= item.count:
                item.delete()
            else:
                item.count -= remove_count
                item.save(update_fields=["count", "updated_at"])
        else:
            basket = self._get_basket_session(request)
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

    def _get_or_create_user_basket(self, user):
        basket, _ = Basket.objects.get_or_create(user=user)
        return basket

    def _get_basket_db(self, user):
        basket_items = (
            BasketItem.objects.filter(basket__user=user)
            .select_related("basket", "product")
            .only("id", "basket_id", "product_id", "count")
            .order_by("id")
        )
        return {str(item.product_id): item.count for item in basket_items}

    def _merge_session_to_db_if_needed(self, request):
        if not request.user.is_authenticated:
            return

        session_basket = self._get_basket_session(request)
        if not session_basket:
            return

        basket = self._get_or_create_user_basket(request.user)
        product_ids = [int(product_id) for product_id in session_basket.keys()]
        valid_product_ids = set(
            Product.objects.filter(id__in=product_ids).values_list("id", flat=True)
        )
        if not valid_product_ids:
            self._set_basket_session(request, {})
            return

        existing_items = {
            item.product_id: item
            for item in BasketItem.objects.filter(
                basket=basket,
                product_id__in=valid_product_ids,
            )
        }

        to_create = []
        to_update = []
        for product_id in valid_product_ids:
            count = session_basket.get(str(product_id), 0)
            if count <= 0:
                continue
            existing_item = existing_items.get(product_id)
            if existing_item is None:
                to_create.append(
                    BasketItem(
                        basket=basket,
                        product_id=product_id,
                        count=count,
                    )
                )
            else:
                existing_item.count += count
                to_update.append(existing_item)

        if to_create:
            BasketItem.objects.bulk_create(to_create)
        if to_update:
            BasketItem.objects.bulk_update(to_update, ["count", "updated_at"])

        self._set_basket_session(request, {})

    def _build_response_items(self, request):
        if request.user.is_authenticated:
            basket = self._get_basket_db(request.user)
        else:
            basket = self._get_basket_session(request)

        if not basket:
            if not request.user.is_authenticated:
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
            if request.user.is_authenticated:
                basket_instance = self._get_or_create_user_basket(request.user)
                BasketItem.objects.filter(basket=basket_instance).exclude(
                    product_id__in=[int(product_id) for product_id in cleaned_basket.keys()]
                ).delete()
            else:
                self._set_basket_session(request, cleaned_basket)

        serializer = BasketItemSerializer(items, many=True)
        return serializer.data
