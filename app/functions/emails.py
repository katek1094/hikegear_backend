from django.urls import reverse
from django.contrib.auth import login
from django.conf import settings
from django.utils.encoding import force_bytes
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.shortcuts import redirect, HttpResponse
from django.utils.encoding import DjangoUnicodeDecodeError

from app.models import MyUser
from hikegear_backend.settings import FRONTEND_URL


def send_account_activation_email(request, user):
    text_content = 'Aktywacja konta'
    subject = 'Aktywacja konta'
    template_name = "activation.html"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipients = [user.email]
    kwargs = {
        "uidb64": urlsafe_base64_encode(force_bytes(user.id)),
        "token": default_token_generator.make_token(user)
    }
    activation_url = reverse("activate_account", kwargs=kwargs)
    activate_url = f"{request.scheme}://{request.get_host()}{activation_url}"
    html_content = render_to_string(template_name, {'activate_url': activate_url})
    email = EmailMultiAlternatives(subject, text_content, from_email, recipients)
    email.attach_alternative(html_content, "text/html")
    email.send()


def send_password_reset_email(user):
    text_content = 'Resetowanie hasła'
    subject = 'Resetowanie hasła'
    template_name = "password_reset_email.html"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipients = [user.email]
    uidb64 = urlsafe_base64_encode(force_bytes(user.id))
    token = default_token_generator.make_token(user)
    reset_url = FRONTEND_URL + 'reset_hasla/' + uidb64 + '/' + token
    html_content = render_to_string(template_name, {'reset_url': reset_url})
    email = EmailMultiAlternatives(subject, text_content, from_email, recipients)
    email.attach_alternative(html_content, "text/html")
    email.send()


def activate_user_account_view(request, uidb64=None, token=None):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = MyUser.objects.get(pk=uid)
    except (MyUser.DoesNotExist, DjangoUnicodeDecodeError, ValueError):
        return HttpResponse('invalid request')
    if default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return redirect(FRONTEND_URL + 'edytor')
    else:
        if not user.is_active:
            user.delete()
            return redirect(FRONTEND_URL + 'link_wygasl')
        else:
            return redirect(FRONTEND_URL + 'logowanie')
