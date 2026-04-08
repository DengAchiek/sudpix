import base64
import json
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from apps.downloads.models import Download

from .models import Payment


class MpesaError(Exception):
    pass


class MpesaConfigurationError(MpesaError):
    pass


class MpesaGatewayError(MpesaError):
    pass


LOCAL_CALLBACK_HOSTS = {"127.0.0.1", "localhost", "0.0.0.0", "::1", "testserver"}


def normalize_phone_number(phone_number):
    digits = "".join(character for character in str(phone_number or "") if character.isdigit())
    if not digits:
        raise MpesaGatewayError("Enter the phone number that should receive the M-Pesa prompt.")

    if digits.startswith("0"):
        digits = f"254{digits[1:]}"
    elif digits.startswith("7") and len(digits) == 9:
        digits = f"254{digits}"
    elif digits.startswith("1") and len(digits) == 9:
        digits = f"254{digits}"

    if not digits.startswith("254") or len(digits) != 12:
        raise MpesaGatewayError("Use a valid Kenyan mobile number like 2547XXXXXXXX.")

    return digits


def build_callback_url(request):
    callback_path = reverse("payments:mpesa_callback")
    if settings.MPESA_CALLBACK_BASE_URL:
        return f"{settings.MPESA_CALLBACK_BASE_URL.rstrip('/')}{callback_path}"
    return request.build_absolute_uri(callback_path)


def validate_callback_url(request):
    callback_url = build_callback_url(request)
    parsed = urlparse(callback_url)
    hostname = (parsed.hostname or "").lower()

    if parsed.scheme != "https":
        raise MpesaConfigurationError(
            "M-Pesa needs a public HTTPS callback URL. Set MPESA_CALLBACK_BASE_URL to your ngrok or deployed HTTPS URL."
        )

    if hostname in LOCAL_CALLBACK_HOSTS:
        raise MpesaConfigurationError(
            "M-Pesa cannot reach a localhost callback URL. Set MPESA_CALLBACK_BASE_URL to a public HTTPS URL such as your ngrok address."
        )

    return callback_url


def prepare_stk_push_request(phone_number, request):
    validate_mpesa_configuration()
    normalized_phone = normalize_phone_number(phone_number)
    callback_url = validate_callback_url(request)
    return normalized_phone, callback_url


def initiate_stk_push(payment, request, account_reference, transaction_desc):
    normalized_phone, callback_url = prepare_stk_push_request(payment.phone_number, request)
    timestamp = build_mpesa_timestamp()
    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": build_mpesa_password(timestamp),
        "Timestamp": timestamp,
        "TransactionType": settings.MPESA_TRANSACTION_TYPE,
        "Amount": format_mpesa_amount(payment.amount),
        "PartyA": normalized_phone,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": normalized_phone,
        "CallBackURL": callback_url,
        "AccountReference": account_reference[:12],
        "TransactionDesc": transaction_desc[:32],
    }

    access_token = get_mpesa_access_token()
    response_payload = make_json_request(
        url=f"{get_mpesa_base_url()}/mpesa/stkpush/v1/processrequest",
        method="POST",
        payload=payload,
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    payment.phone_number = normalized_phone
    payment.merchant_request_id = response_payload.get("MerchantRequestID", "")
    payment.checkout_request_id = response_payload.get("CheckoutRequestID", "")
    payment.gateway_response_code = str(response_payload.get("ResponseCode", ""))
    payment.gateway_response_message = response_payload.get("ResponseDescription", "")
    payment.result_desc = response_payload.get("CustomerMessage", "")
    payment.raw_response = response_payload
    payment.prompt_sent_at = timezone.now()
    payment.status = Payment.Status.PENDING
    payment.save(
        update_fields=[
            "phone_number",
            "merchant_request_id",
            "checkout_request_id",
            "gateway_response_code",
            "gateway_response_message",
            "result_desc",
            "raw_response",
            "prompt_sent_at",
            "status",
        ]
    )

    if str(response_payload.get("ResponseCode", "")) != "0":
        raise MpesaGatewayError(
            response_payload.get("ResponseDescription") or "M-Pesa did not accept the payment request."
        )

    return response_payload


def handle_stk_callback(payload):
    stk_callback = payload.get("Body", {}).get("stkCallback") or {}
    checkout_request_id = stk_callback.get("CheckoutRequestID", "")
    merchant_request_id = stk_callback.get("MerchantRequestID", "")
    if not checkout_request_id and not merchant_request_id:
        raise MpesaGatewayError("Missing checkout identifiers in callback payload.")

    payment = Payment.objects.filter(
        checkout_request_id=checkout_request_id
    ).first()
    if payment is None and merchant_request_id:
        payment = Payment.objects.filter(merchant_request_id=merchant_request_id).first()
    if payment is None:
        raise Payment.DoesNotExist("No payment matches this callback.")

    metadata = extract_callback_metadata(stk_callback)
    result_code = int(stk_callback.get("ResultCode", 1))
    result_desc = stk_callback.get("ResultDesc", "")

    payment.raw_response = payload
    payment.result_code = result_code
    payment.result_desc = result_desc
    payment.merchant_request_id = merchant_request_id or payment.merchant_request_id
    payment.checkout_request_id = checkout_request_id or payment.checkout_request_id
    payment.gateway_response_message = result_desc

    if metadata.get("PhoneNumber"):
        payment.phone_number = str(metadata["PhoneNumber"])

    if result_code == 0:
        payment.status = Payment.Status.CONFIRMED
        payment.paid_at = timezone.now()
        if metadata.get("MpesaReceiptNumber"):
            payment.reference = str(metadata["MpesaReceiptNumber"])
        unlock_downloads_for_payment(payment)
    else:
        payment.status = Payment.Status.FAILED
        payment.paid_at = None
        lock_downloads_for_payment(payment)

    payment.save(
        update_fields=[
            "raw_response",
            "result_code",
            "result_desc",
            "merchant_request_id",
            "checkout_request_id",
            "gateway_response_message",
            "phone_number",
            "status",
            "paid_at",
            "reference",
        ]
    )
    return payment


def extract_callback_metadata(stk_callback):
    metadata_items = stk_callback.get("CallbackMetadata", {}).get("Item", [])
    metadata = {}
    for item in metadata_items:
        name = item.get("Name")
        if name:
            metadata[name] = item.get("Value")
    return metadata


def unlock_downloads_for_payment(payment):
    Download.objects.filter(payment=payment).update(
        status=Download.Status.READY,
        available_at=timezone.now(),
    )


def lock_downloads_for_payment(payment):
    Download.objects.filter(payment=payment).update(
        status=Download.Status.LOCKED,
        available_at=None,
    )


def validate_mpesa_configuration():
    missing = [
        name
        for name, value in {
            "MPESA_CONSUMER_KEY": settings.MPESA_CONSUMER_KEY,
            "MPESA_CONSUMER_SECRET": settings.MPESA_CONSUMER_SECRET,
            "MPESA_SHORTCODE": settings.MPESA_SHORTCODE,
            "MPESA_PASSKEY": settings.MPESA_PASSKEY,
        }.items()
        if not value
    ]
    if missing:
        missing_fields = ", ".join(missing)
        raise MpesaConfigurationError(
            f"M-Pesa is not configured yet. Add {missing_fields} in your environment settings."
        )


def get_mpesa_access_token():
    credentials = f"{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}".encode()
    authorization = base64.b64encode(credentials).decode()
    response_payload = make_json_request(
        url=f"{get_mpesa_base_url()}/oauth/v1/generate?grant_type=client_credentials",
        headers={
            "Authorization": f"Basic {authorization}",
        },
    )
    access_token = response_payload.get("access_token", "")
    if not access_token:
        raise MpesaGatewayError("M-Pesa did not return an access token.")
    return access_token


def build_mpesa_password(timestamp):
    password_source = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
    return base64.b64encode(password_source.encode()).decode()


def build_mpesa_timestamp():
    return datetime.now(ZoneInfo("Africa/Nairobi")).strftime("%Y%m%d%H%M%S")


def format_mpesa_amount(amount):
    return int(Decimal(amount).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def get_mpesa_base_url():
    if settings.MPESA_ENVIRONMENT == "production":
        return "https://api.safaricom.co.ke"
    return "https://sandbox.safaricom.co.ke"


def make_json_request(url, method="GET", payload=None, headers=None):
    request_headers = {
        "Accept": "application/json",
    }
    if payload is not None:
        request_headers["Content-Type"] = "application/json"
    if headers:
        request_headers.update(headers)

    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    request = Request(url=url, data=data, method=method, headers=request_headers)

    try:
        with urlopen(request, timeout=settings.MPESA_TIMEOUT) as response:
            response_body = response.read().decode("utf-8") or "{}"
    except HTTPError as exc:
        response_body = exc.read().decode("utf-8", errors="ignore")
        raise MpesaGatewayError(parse_gateway_error(response_body) or f"M-Pesa request failed with HTTP {exc.code}.") from exc
    except URLError as exc:
        raise MpesaGatewayError("Could not reach the M-Pesa gateway. Check your internet connection and callback URL.") from exc

    try:
        return json.loads(response_body)
    except json.JSONDecodeError as exc:
        raise MpesaGatewayError("M-Pesa returned an invalid response.") from exc


def parse_gateway_error(response_body):
    try:
        payload = json.loads(response_body or "{}")
    except json.JSONDecodeError:
        return ""
    return (
        payload.get("errorMessage")
        or payload.get("ResponseDescription")
        or payload.get("error_description")
        or ""
    )
