from django.urls import re_path

from catalog.views import (
    BannersAPIView,
    CatalogListAPIView,
    CategoriesListAPIView,
    LimitedProductsAPIView,
    PopularProductsAPIView,
    ProductDetailAPIView,
    SalesAPIView,
)

urlpatterns = [
    re_path(r"^categories/?$", CategoriesListAPIView.as_view(), name="categories-list"),
    re_path(r"^catalog/?$", CatalogListAPIView.as_view(), name="catalog-list"),
    re_path(
        r"^products/popular/?$",
        PopularProductsAPIView.as_view(),
        name="products-popular",
    ),
    re_path(
        r"^products/limited/?$",
        LimitedProductsAPIView.as_view(),
        name="products-limited",
    ),
    re_path(r"^banners/?$", BannersAPIView.as_view(), name="banners"),
    re_path(r"^sales/?$", SalesAPIView.as_view(), name="sales"),
    re_path(
        r"^product/(?P<product_id>\d+)/?$",
        ProductDetailAPIView.as_view(),
        name="product-detail",
    ),
]
