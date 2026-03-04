from django.urls import path

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
    path("categories", CategoriesListAPIView.as_view(), name="categories-list"),
    path("categories/", CategoriesListAPIView.as_view(), name="categories-list-slash"),
    path("catalog", CatalogListAPIView.as_view(), name="catalog-list"),
    path("catalog/", CatalogListAPIView.as_view(), name="catalog-list-slash"),
    path("products/popular", PopularProductsAPIView.as_view(), name="products-popular"),
    path(
        "products/popular/",
        PopularProductsAPIView.as_view(),
        name="products-popular-slash",
    ),
    path("products/limited", LimitedProductsAPIView.as_view(), name="products-limited"),
    path(
        "products/limited/",
        LimitedProductsAPIView.as_view(),
        name="products-limited-slash",
    ),
    path("banners", BannersAPIView.as_view(), name="banners"),
    path("banners/", BannersAPIView.as_view(), name="banners-slash"),
    path("sales", SalesAPIView.as_view(), name="sales"),
    path("sales/", SalesAPIView.as_view(), name="sales-slash"),
    path("product/<int:product_id>", ProductDetailAPIView.as_view(), name="product-detail"),
    path(
        "product/<int:product_id>/",
        ProductDetailAPIView.as_view(),
        name="product-detail-slash",
    ),
]
