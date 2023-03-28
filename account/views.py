from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage, send_mail, get_connection
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views import View
from rest_framework.authtoken.models import Token

from account.exceptions import DuplicateException, ActivateException
from account.forms import SignupForm, LoginForm
from account.serializer import UserSerializer
from account.tokens import account_activation_token
from utils.constants import HttpStatusCode, HttpErrorMsg
from utils.http_response import send_http_response
from account.models import User as Account_User
from django.conf import settings

from utils.util import format_serializer_data, send_activation_mail, get_curr_timestamp_utc


def home(request):
    return render(request, 'home.html')


class UserSignUpView(View):
    form_class = SignupForm
    initial = {'key': 'value'}
    template_name = 'signup.html'

    def post(self, request, *args, **kwargs):
        try:
            form = SignupForm(request.POST)
            print(form.is_valid())
            if form.is_valid():
                to_email = form.cleaned_data.get('email')
                user_qs = User.objects.filter(email=to_email).filter(is_deleted=False)
                user_s = UserSerializer(user_qs, many=True)
                user_data = format_serializer_data(user_s)
                if user_data:
                    if user_data[0]['is_activated']:
                        raise DuplicateException
                    else:
                        raise ActivateException

                user = form.save()
                user.is_active = False
                user.save()
                new_user = User(username=user.username, email=user.email)
                new_user.save()
                send_activation_mail(request, user, form)
                return render(request, 'acc_active_sent.html', {'form': form})

            return render(request, self.template_name, {'form': form})

        except DuplicateException as de:
            print('Duplicate mail id found!!')
            form = LoginForm()
            context = {'form': form, 'error': True, 'err_msg': 'Account already exists!! Try signing in'}
            return render(request, 'login.html', context)

        except ActivateException as ae:
            form = SignupForm()
            print('User exists activation required')
            return render(request, 'acc_active_sent.html', {'form': form})

        except Exception as e:
            print(f'Exception occurred due to: {e}')
            return send_http_response(status=HttpStatusCode['SERVER_ERROR'], err_msg=HttpErrorMsg['SERVER_ERROR'])

    def get(self, request):
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {'form': form})


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        account_user = Account_User.objects.filter(request.username)
        account_user.is_activated = True
        account_user.updated_at = get_curr_timestamp_utc()
        account_user.save()
        return send_http_response(data='Thank you for your email confirmation. Now you can login your account.')
    else:
        return send_http_response(data='Activation link is invalid!')


class CustomLoginView(LoginView):
    form_class = LoginForm

    def form_valid(self, form):
        return super(CustomLoginView, self).form_valid(form)


@login_required
def profile(request):
    print('request:', request, request.user, request.POST)
    generate_token = request.POST.get('generate_token')
    print(generate_token)
    token = False
    token_value = None
    if generate_token:
        token = True
        new_token, created = Token.objects.get_or_create(user=request.user)
        token_value = new_token.key
    context = {'token': token, 'token_value': token_value}
    return render(request, 'profile.html', context)
