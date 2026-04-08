import json
from datetime import date
from decimal import Decimal
import tempfile
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.media_management.models import MediaAsset
from apps.projects.models import Project

from .models import Payment
from .services import (
    MpesaConfigurationError,
    initiate_stk_push,
    normalize_phone_number,
    prepare_stk_push_request,
)


class MockGatewayResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def read(self):
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class MpesaPaymentTests(TestCase):
    def setUp(self):
        self.temp_media = tempfile.TemporaryDirectory()
        self.media_override = self.settings(
            MEDIA_ROOT=self.temp_media.name,
            MEDIA_URL="/media/",
            MPESA_CONSUMER_KEY="test-key",
            MPESA_CONSUMER_SECRET="test-secret",
            MPESA_SHORTCODE="174379",
            MPESA_PASSKEY="test-passkey",
            MPESA_CALLBACK_BASE_URL="https://example.com",
        )
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)
        self.addCleanup(self.temp_media.cleanup)

        self.user = get_user_model().objects.create_user(
            username="payclient",
            email="payclient@example.com",
            password="testpass123",
        )
        self.project = Project.objects.create(
            client=self.user,
            title="Phone Prompt Gallery",
            slug="phone-prompt-gallery",
            service_type="Photography",
            status=Project.Status.READY,
            shoot_date=date(2026, 3, 28),
        )
        self.media_asset = MediaAsset.objects.create(
            project=self.project,
            title="Prompt Portrait.jpg",
            kind=MediaAsset.Kind.PHOTO,
            file=SimpleUploadedFile(
                "prompt-portrait.jpg",
                b"portrait",
                content_type="image/jpeg",
            ),
        )
        self.payment = Payment.objects.create(
            user=self.user,
            project=self.project,
            amount=Decimal("80.00"),
            method=Payment.Method.MPESA,
            status=Payment.Status.PENDING,
            phone_number="0712345678",
        )
        self.payment.media_assets.add(self.media_asset)

    def test_normalize_phone_number_converts_local_format(self):
        self.assertEqual(normalize_phone_number("0712345678"), "254712345678")
        self.assertEqual(normalize_phone_number("+254 712 345 678"), "254712345678")

    def test_prepare_stk_push_request_requires_public_https_callback_url(self):
        callback_settings = self.settings(MPESA_CALLBACK_BASE_URL="")
        callback_settings.enable()
        self.addCleanup(callback_settings.disable)
        request = RequestFactory().post("/client/checkout/")

        with self.assertRaisesMessage(
            MpesaConfigurationError,
            "M-Pesa needs a public HTTPS callback URL.",
        ):
            prepare_stk_push_request("0712345678", request)

    @patch("apps.payments.services.urlopen")
    def test_initiate_stk_push_updates_payment_with_gateway_ids(self, mock_urlopen):
        mock_urlopen.side_effect = [
            MockGatewayResponse({"access_token": "token-123"}),
            MockGatewayResponse(
                {
                    "MerchantRequestID": "merchant-001",
                    "CheckoutRequestID": "checkout-001",
                    "ResponseCode": "0",
                    "ResponseDescription": "Success. Request accepted for processing",
                    "CustomerMessage": "Success. Request accepted for processing",
                }
            ),
        ]
        request = RequestFactory().post("/client/checkout/")

        response = initiate_stk_push(
            payment=self.payment,
            request=request,
            account_reference="SudPix80",
            transaction_desc="SudPix file payment",
        )

        self.payment.refresh_from_db()
        self.assertEqual(response["ResponseCode"], "0")
        self.assertEqual(self.payment.phone_number, "254712345678")
        self.assertEqual(self.payment.merchant_request_id, "merchant-001")
        self.assertEqual(self.payment.checkout_request_id, "checkout-001")
        self.assertEqual(self.payment.status, Payment.Status.PENDING)
        self.assertIsNotNone(self.payment.prompt_sent_at)

    def test_mpesa_callback_marks_payment_confirmed(self):
        self.payment.checkout_request_id = "ws_CO_123"
        self.payment.merchant_request_id = "merchant-123"
        self.payment.save(update_fields=["checkout_request_id", "merchant_request_id"])

        payload = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "merchant-123",
                    "CheckoutRequestID": "ws_CO_123",
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": 80},
                            {"Name": "MpesaReceiptNumber", "Value": "QWE123ABC"},
                            {"Name": "TransactionDate", "Value": 20260328120000},
                            {"Name": "PhoneNumber", "Value": 254712345678},
                        ]
                    },
                }
            }
        }

        response = self.client.post(
            reverse("payments:mpesa_callback"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.CONFIRMED)
        self.assertEqual(self.payment.reference, "QWE123ABC")
        self.assertEqual(self.payment.result_code, 0)
        self.assertEqual(self.payment.phone_number, "254712345678")
