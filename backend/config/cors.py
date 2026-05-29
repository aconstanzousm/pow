from django.http import HttpRequest, HttpResponse


class SimpleCorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        origin = request.headers.get("Origin")
        if request.method == "OPTIONS" and origin:
            response = HttpResponse(status=204)
            self._apply_headers(response, origin, request.headers.get("Access-Control-Request-Headers"))
            return response

        response = self.get_response(request)
        if origin:
            self._apply_headers(response, origin, None)
        return response

    def _apply_headers(self, response: HttpResponse, origin: str, requested_headers: str | None) -> None:
        allowed = {
            "null",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
        }
        response["Access-Control-Allow-Origin"] = origin if origin in allowed else "null"
        response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response["Access-Control-Allow-Headers"] = requested_headers or "Authorization, Content-Type, Accept"
        response["Access-Control-Max-Age"] = "600"
