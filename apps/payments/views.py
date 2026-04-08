import json

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .services import MpesaError, handle_stk_callback


@method_decorator(csrf_exempt, name="dispatch")
class MpesaCallbackView(View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return JsonResponse(
                {"ResultCode": 1, "ResultDesc": "Invalid JSON payload."},
                status=400,
            )

        try:
            handle_stk_callback(payload)
        except MpesaError as exc:
            return JsonResponse(
                {"ResultCode": 1, "ResultDesc": str(exc)},
                status=400,
            )
        except Exception:
            return JsonResponse(
                {"ResultCode": 1, "ResultDesc": "Callback processing failed."},
                status=400,
            )

        return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})
