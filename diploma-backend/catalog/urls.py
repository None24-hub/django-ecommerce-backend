from django.urls import path

from catalog.views import CatalogListAPIView, CategoriesListAPIView, ProductDetailAPIView

urlpatterns = [
    path("categories", CategoriesListAPIView.as_view(), name="categories-list"),
    path("categories/", CategoriesListAPIView.as_view(), name="categories-list-slash"),
    path("catalog", CatalogListAPIView.as_view(), name="catalog-list"),
    path("catalog/", CatalogListAPIView.as_view(), name="catalog-list-slash"),
    path("product/<int:product_id>", ProductDetailAPIView.as_view(), name="product-detail"),
    path(
        "product/<int:product_id>/",
        ProductDetailAPIView.as_view(),
        name="product-detail-slash",
    ),
]
