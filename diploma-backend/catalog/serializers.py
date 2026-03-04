from rest_framework import serializers

from catalog.models import Category, Product, ProductImage, Review, Specification, Tag


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ("src", "alt")


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name")


class ReviewSerializer(serializers.ModelSerializer):
    date = serializers.DateTimeField(source="created_at", format="%Y-%m-%d %H:%M")

    class Meta:
        model = Review
        fields = ("author", "email", "text", "rate", "date")


class SpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specification
        fields = ("name", "value")


class ProductShortSerializer(serializers.ModelSerializer):
    category = serializers.IntegerField(source="category_id")
    date = serializers.DateTimeField(source="created_at", format="%Y-%m-%d %H:%M:%S")
    freeDelivery = serializers.BooleanField(source="free_delivery")
    images = ImageSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Product
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
            "tags",
            "reviews",
            "rating",
        )

    def get_reviews(self, obj):
        value = getattr(obj, "reviews_count", None)
        if value is None:
            return obj.reviews.count()
        return int(value)

    def get_rating(self, obj):
        value = getattr(obj, "rating_value", None)
        if value is None:
            value = obj.rating
        return float(value or 0)


class ProductFullSerializer(serializers.ModelSerializer):
    category = serializers.IntegerField(source="category_id")
    date = serializers.DateTimeField(source="created_at", format="%Y-%m-%d %H:%M:%S")
    fullDescription = serializers.CharField(source="full_description")
    freeDelivery = serializers.BooleanField(source="free_delivery")
    images = ImageSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    specifications = SpecificationSerializer(many=True, read_only=True)
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "category",
            "price",
            "count",
            "date",
            "title",
            "description",
            "fullDescription",
            "freeDelivery",
            "images",
            "tags",
            "reviews",
            "specifications",
            "rating",
        )

    def get_rating(self, obj):
        value = getattr(obj, "rating_value", None)
        if value is None:
            value = obj.rating
        return float(value or 0)


class SaleItemSerializer(serializers.ModelSerializer):
    id = serializers.CharField()
    salePrice = serializers.DecimalField(
        source="sale_price",
        max_digits=10,
        decimal_places=2,
    )
    dateFrom = serializers.DateField(source="sale_date_from", format="%m-%d")
    dateTo = serializers.DateField(source="sale_date_to", format="%m-%d")
    images = ImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "price",
            "salePrice",
            "dateFrom",
            "dateTo",
            "title",
            "images",
        )


class CategoryBaseSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ("id", "title", "image")

    def get_image(self, obj):
        if not obj.image_src:
            return None
        return {"src": obj.image_src, "alt": obj.image_alt}


class CategorySerializer(CategoryBaseSerializer):
    subcategories = CategoryBaseSerializer(many=True, read_only=True)

    class Meta(CategoryBaseSerializer.Meta):
        fields = ("id", "title", "image", "subcategories")
