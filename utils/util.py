import datetime
import json

from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage, get_connection
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from account.tokens import account_activation_token

from django.conf import settings


def format_serializer_data(serializer_data):
    return json.loads(json.dumps(serializer_data))


def send_activation_mail(request, user, form):
    try:
        current_site = get_current_site(request)
        message = render_to_string('acc_active_email.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user),
            'protocol': 'https' if request.is_secure() else 'http',
        })
        mail_subject = 'Activate your account.'
        to_email = form.cleaned_data.get('email')
        print('to email:', to_email)
        with get_connection(
                host=settings.EMAIL_HOST,
                port=settings.EMAIL_PORT,
                username=settings.EMAIL_HOST_USER,
                password=settings.EMAIL_HOST_PASSWORD,
                use_tls=settings.EMAIL_USE_TLS,
                timeout=30,
        ) as connection:
            email = EmailMessage(mail_subject, message, to=[to_email], connection=connection)
            print('email:', email)
            email.send()
    except Exception as e:
        print(f'Exception occurred due to: {e}')


def get_curr_timestamp_utc():
    return datetime.datetime.now(datetime.timezone.utc)
