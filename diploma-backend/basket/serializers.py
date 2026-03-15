from rest_framework import serializers

from catalog.serializers import ProductShortSerializer


class BasketItemSerializer(ProductShortSerializer):
    count = serializers.SerializerMethodField()

    def get_count(self, obj):
        return int(getattr(obj, "basket_count", 0))
