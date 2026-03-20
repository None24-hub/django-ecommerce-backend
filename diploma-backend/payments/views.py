from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Order
from payments.models import Payment
from payments.serializers import PaymentRequestSerializer


class PaymentProcessAPIView(APIView):
    anon_orders_session_key = "order_ids"

    def post(self, request, order_id):
        order = self._get_accessible_order(request, order_id)

        serializer = PaymentRequestSerializer(data=request.data)
        if not serializer.is_valid():
            self._mark_payment_failed(order, "Invalid payment data.")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        payment_data = serializer.validated_data
        payment, _ = Payment.objects.get_or_create(order=order)
        payment.status = Payment.STATUS_SUCCEEDED
        payment.holder_name = payment_data["name"]
        payment.card_number_masked = self._mask_card_number(payment_data["number"])
        payment.exp_month = payment_data["month"]
        payment.exp_year = payment_data["year"]
        payment.error_message = ""
        payment.processed_at = timezone.now()
        payment.save(
            update_fields=[
                "status",
                "holder_name",
                "card_number_masked",
                "exp_month",
                "exp_year",
                "error_message",
                "processed_at",
                "updated_at",
            ]
        )

        if order.status != "paid":
            order.status = "paid"
            order.save(update_fields=["status", "updated_at"])

        return Response(status=status.HTTP_200_OK)

    def _get_accessible_order(self, request, order_id):
        filters = Q(id=order_id)
        if request.user.is_authenticated:
            filters &= Q(user=request.user)
        else:
            order_ids = request.session.get(self.anon_orders_session_key, [])
            if not isinstance(order_ids, list):
                order_ids = []
            valid_order_ids = [value for value in order_ids if isinstance(value, int)]
            filters &= Q(id__in=valid_order_ids)

        queryset = Order.objects.select_related("payment").only(
            "id",
            "user_id",
            "status",
            "payment__id",
            "payment__status",
            "payment__error_message",
        )
        return get_object_or_404(queryset, filters)

    def _mark_payment_failed(self, order, error_message):
        payment, _ = Payment.objects.get_or_create(order=order)
        payment.status = Payment.STATUS_FAILED
        payment.error_message = error_message
        payment.processed_at = timezone.now()
        payment.save(
            update_fields=[
                "status",
                "error_message",
                "processed_at",
                "updated_at",
            ]
        )

        if order.status != "paid":
            order.status = "payment_failed"
            order.save(update_fields=["status", "updated_at"])

    @staticmethod
    def _mask_card_number(number):
        return f"**** **** **** {number[-4:]}"
