from django.contrib import admin

from payments.models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "order_id", "status", "holder_name", "processed_at")
    search_fields = ("id", "order_id", "holder_name", "card_number_masked")
    list_filter = ("status",)
