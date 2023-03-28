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
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated

from account.exceptions import DuplicateException, ActivateException
from account.forms import SignupForm, LoginForm
from account.serializer import UserSerializer, UserAPITokenSerializer
from account.tokens import account_activation_token
from utils.constants import HttpStatusCode, HttpErrorMsg, WEATHER_API_URL
from utils.http_request import make_get_request
from utils.http_response import send_http_response
from account.models import User as Account_User, UserAPIToken
from django.conf import settings

from utils.util import format_serializer_data, send_activation_mail, get_curr_timestamp_utc


def home(request):
    return render(request, 'home.html')


class UserSignUpView(View):
    form_class = SignupForm
    initial = {'key': 'value'}
    template_name = 'signup.html'

    def post(self, request, *args, **kwargs):
        form = SignupForm(request.POST)
        try:
            print(form.is_valid())
            to_email = form.cleaned_data.get('email')
            user_qs = Account_User.objects.filter(email=to_email).filter(is_deleted=False)
            user_s = UserSerializer(user_qs, many=True)
            # print(user_s)
            user_data = format_serializer_data(user_s.data)
            if user_data:
                if user_data[0]['is_activated']:
                    raise DuplicateException
                else:
                    raise ActivateException
            if form.is_valid():
                user = form.save()
                user.is_active = False
                user.save()
                new_user = Account_User(username=user.username, email=user.email)
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
            print('User exists activation required')
            print(request.POST.get('username'))
            user = User.objects.get(username=request.POST.get('username'))
            send_activation_mail(request, user, form)
            context = {'error': True, 'err_msg': 'User exists activation required'}
            return render(request, 'acc_active_sent.html', context)

        except Exception as e:
            print(f'Exception occurred due to: {e}')
            return render(request, self.template_name, {'form': form})

    def get(self, request):
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {'form': form})


def activate(request, uidb64, token):
    try:
        print(request, request.GET)
        uid = force_str(urlsafe_base64_decode(uidb64))
        print('uid:', uid)
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        account_user = Account_User.objects.get(username=user.username)
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
    account_user = Account_User.objects.get(username=request.user)
    user_token_qs = UserAPIToken.objects.filter(user_id=account_user.id).filter(is_deleted=False)
    user_token_s = UserAPITokenSerializer(user_token_qs, many=True)
    user_token_data = format_serializer_data(user_token_s.data)
    if user_token_data:
        token = True
        token_value = user_token_data[0]['token']
    if generate_token:
        token = True
        new_token, created = Token.objects.get_or_create(user=request.user)
        token_value = new_token.key
        user_token = UserAPIToken(user_id=account_user, token=token_value)
        user_token.save()

    context = {'token': token, 'token_value': token_value}
    return render(request, 'profile.html', context)


class WeatherDetailsView(View):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_weather_data(self, region):
        url = f'{WEATHER_API_URL}&q={region}'
        weather_data = make_get_request(url)
        return weather_data

    def get(self, request):
        try:
            region = request.GET.get('region')
            weather_data = self.get_weather_data(region)
            return send_http_response(data=weather_data)
        except Exception as e:
            print(f'Exception due to: {e}')
            return send_http_response(status=HttpStatusCode['SERVER_ERROR'], err_msg=HttpErrorMsg['SERVER_ERROR'])
