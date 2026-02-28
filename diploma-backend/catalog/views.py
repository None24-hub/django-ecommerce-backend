import math

from django.db.models import Avg, Count, F, FloatField, Prefetch, Q, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import Category, Product, ProductImage, Review, Specification, Tag
from catalog.serializers import CategorySerializer, ProductFullSerializer, ProductShortSerializer


def _to_bool(raw_value):
    if raw_value is None:
        return None
    value = str(raw_value).strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    return None


def _to_int(raw_value, default):
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return default


def _to_float(raw_value):
    try:
        return float(raw_value)
    except (TypeError, ValueError):
        return None


class CategoriesListAPIView(APIView):
    def get(self, request):
        subcategories_qs = Category.objects.only(
            "id",
            "title",
            "image_src",
            "image_alt",
            "parent_id",
        ).order_by("id")
        categories = (
            Category.objects.filter(parent__isnull=True)
            .only("id", "title", "image_src", "image_alt")
            .prefetch_related(Prefetch("subcategories", queryset=subcategories_qs))
        )
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)


class CatalogListAPIView(APIView):
    SORT_FIELDS = {
        "rating": "rating_value",
        "price": "price",
        "reviews": "reviews_count",
        "date": "created_at",
    }

    def get(self, request):
        query_params = request.query_params

        products = (
            Product.objects.select_related("category")
            .only(
                "id",
                "category_id",
                "title",
                "description",
                "price",
                "count",
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

        text_filter = query_params.get("filter[name]") or query_params.get("filter")
        if text_filter:
            products = products.filter(title__icontains=text_filter)

        min_price = _to_float(query_params.get("filter[minPrice]"))
        if min_price is not None:
            products = products.filter(price__gte=min_price)

        max_price = _to_float(query_params.get("filter[maxPrice]"))
        if max_price is not None:
            products = products.filter(price__lte=max_price)

        free_delivery = _to_bool(query_params.get("filter[freeDelivery]"))
        if free_delivery is True:
            products = products.filter(free_delivery=True)

        available = _to_bool(query_params.get("filter[available]"))
        if available is True:
            products = products.filter(count__gt=0)

        category_id = _to_int(query_params.get("category"), None)
        if category_id is not None:
            category_ids = Category.objects.filter(
                Q(id=category_id) | Q(parent_id=category_id)
            ).values_list("id", flat=True)
            products = products.filter(category_id__in=category_ids)

        tags = query_params.getlist("tags[]") or query_params.getlist("tags")
        if tags:
            tag_ids = [tag_id for tag_id in tags if str(tag_id).isdigit()]
            if tag_ids:
                products = products.filter(tags__id__in=tag_ids).distinct()

        sort_field = self.SORT_FIELDS.get(query_params.get("sort"), "created_at")
        sort_type = query_params.get("sortType", "dec")
        sort_prefix = "" if sort_type == "inc" else "-"
        products = products.order_by(f"{sort_prefix}{sort_field}", f"{sort_prefix}id")

        current_page = max(_to_int(query_params.get("currentPage"), 1), 1)
        limit = _to_int(query_params.get("limit"), 20)
        limit = 20 if limit <= 0 else min(limit, 100)

        total = products.count()
        last_page = max(math.ceil(total / limit), 1)
        current_page = min(current_page, last_page)

        start = (current_page - 1) * limit
        end = start + limit
        serializer = ProductShortSerializer(products[start:end], many=True)

        return Response(
            {
                "items": serializer.data,
                "currentPage": current_page,
                "lastPage": last_page,
            }
        )


class ProductDetailAPIView(APIView):
    def get(self, request, product_id):
        product_qs = (
            Product.objects.select_related("category")
            .only(
                "id",
                "category_id",
                "title",
                "description",
                "full_description",
                "price",
                "count",
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
                Prefetch(
                    "reviews",
                    queryset=Review.objects.only(
                        "id",
                        "product_id",
                        "author",
                        "email",
                        "text",
                        "rate",
                        "created_at",
                    ),
                ),
                Prefetch(
                    "specifications",
                    queryset=Specification.objects.only(
                        "id",
                        "product_id",
                        "name",
                        "value",
                    ),
                ),
            )
            .annotate(
                rating_value=Coalesce(
                    Avg("reviews__rate"),
                    F("rating"),
                    Value(0.0),
                    output_field=FloatField(),
                )
            )
        )
        product = get_object_or_404(product_qs, id=product_id)
        serializer = ProductFullSerializer(product)
        return Response(serializer.data)
