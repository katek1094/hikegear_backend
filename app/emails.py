from django.urls import reverse
from django.contrib.auth import login
from django.conf import settings
from django.utils.encoding import force_bytes
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.shortcuts import redirect, render, HttpResponse

from .models import MyUser
from hikegear_backend.settings import FRONTEND_URL


def send_account_activation_email(request, user):
    text_content = 'Account Activation Email'
    subject = 'Account Activation'
    template_name = "activation.html"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipients = [user.email]
    kwargs = {
        "uidb64": urlsafe_base64_encode(force_bytes(user.id)),
        "token": default_token_generator.make_token(user)
    }
    activation_url = reverse("activate_account", kwargs=kwargs)
    activate_url = f"{request.scheme}://{request.get_host()}{activation_url}"
    context = {'user': user, 'activate_url': activate_url}
    html_content = render_to_string(template_name, context)
    email = EmailMultiAlternatives(subject, text_content, from_email, recipients)
    email.attach_alternative(html_content, "text/html")
    email.send()


def activate_user_account(request, uidb64=None, token=None):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = MyUser.objects.get(pk=uid)
    except MyUser.DoesNotExist:
        return HttpResponse('invalid request')
    if default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return redirect(FRONTEND_URL)
    else:
        user.delete()
        return render(request, 'activation_link_expired.html', {'register_url': FRONTEND_URL + 'register'})
