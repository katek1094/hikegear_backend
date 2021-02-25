from hikegear_backend.settings import FRONTEND_URL


def frontend_url(request):
    return {"frontend_url": FRONTEND_URL}
