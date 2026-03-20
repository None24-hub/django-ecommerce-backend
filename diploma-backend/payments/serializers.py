import re

from rest_framework import serializers


class PaymentRequestSerializer(serializers.Serializer):
    number = serializers.CharField(max_length=32)
    name = serializers.CharField(max_length=255)
    month = serializers.CharField(max_length=2)
    year = serializers.CharField(max_length=2)
    code = serializers.CharField(max_length=3)

    def validate_number(self, value):
        digits = re.sub(r"\D", "", value or "")
        if len(digits) != 16:
            raise serializers.ValidationError("Invalid card number.")
        return digits

    def validate_name(self, value):
        cleaned = (value or "").strip()
        if not cleaned:
            raise serializers.ValidationError("Card holder name is required.")
        return cleaned

    def validate_month(self, value):
        if not re.fullmatch(r"\d{2}", value or ""):
            raise serializers.ValidationError("Month must be in MM format.")
        month = int(value)
        if month < 1 or month > 12:
            raise serializers.ValidationError("Invalid month.")
        return value

    def validate_year(self, value):
        if not re.fullmatch(r"\d{2}", value or ""):
            raise serializers.ValidationError("Year must be in YY format.")
        return value

    def validate_code(self, value):
        if not re.fullmatch(r"\d{3}", value or ""):
            raise serializers.ValidationError("CVV must contain 3 digits.")
        return value
