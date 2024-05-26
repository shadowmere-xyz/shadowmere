from django.http import JsonResponse


def ratelimited_error(request, exception):
    return JsonResponse({"error": "Too many requests"}, status=429)
