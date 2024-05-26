from django.http import HttpResponse


def healthcheck(request):
    return HttpResponse(b"OK")
