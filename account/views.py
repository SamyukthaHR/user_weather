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

from account.exceptions import DuplicateException, ActivateException
from account.forms import SignupForm, LoginForm
from account.serializer import UserSerializer
from account.tokens import account_activation_token
from utils.constants import HttpStatusCode, HttpErrorMsg
from utils.http_response import send_http_response

from django.conf import settings

from utils.util import format_serializer_data


class UserSignUpView(View):
    form_class = SignupForm
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
                if user_s:
                    if user_s[0]['is_activated']:
                        raise DuplicateException
                    else:
                        raise ActivateException

                user = form.save(commit=False)
                user.is_active = False
                user.save()

                current_site = get_current_site(request)
                message = render_to_string('acc_active_email.html', {
                    'user': user, 'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': account_activation_token.make_token(user),
                })
                # Sending activation link in terminal
                # user.email_user(subject, message)
                mail_subject = 'Activate your Weather account.'
                print('to_email:', to_email)
                email = EmailMessage(mail_subject, message, to=[to_email])
                email.send()
                data = {
                    'msg': 'Please confirm your email address to complete the registration.'
                }
                return send_http_response(data=data)
            else:
                form = SignupForm()
                context = {'form': form}
                return render(request, 'signup.html', context)
                # return send_http_response(status=HttpStatusCode['SERVER_ERROR'], err_msg=HttpErrorMsg['SERVER_ERROR'])

        except DuplicateException as de:
            print('Duplicate mail id found!!')
            form = LoginForm()
            form['errors'] = True
            form['err_msg'] = 'Account already exists!! Try signing in'
            context = {'form': form}
            return render(request, 'login.html', context)

        except ActivateException as ae:
            print('User exists activation required')
            return render(request, 'acc_active_sent.html', {'form': form})

        except Exception as e:
            print(f'Exception occurred due to: {e}')
            return send_http_response(status=HttpStatusCode['SERVER_ERROR'], err_msg=HttpErrorMsg['SERVER_ERROR'])


def home(request):
    return render(request, 'home.html')


# def login(request):
#     print(request)
#     # user = User.objects.get(username=request)
#     # redirect(request, 'login.html')
#     return send_http_response(data='Success')


@login_required
def profile(request):
    return render(request, 'profile.html')


def signup(request):
    try:
        if request.method == 'POST':
            form = SignupForm(request.POST)
            print(form.is_valid())
            if form.is_valid():
                user = form.save()
                user.refresh_from_db()
                user.save()
                print('after save:', user, user.pk)
                form = LoginForm()
                # form.errors = {'exists': 'Account already exists!! Try signing in'}
                context = {'form': form}
                return render(request, 'login.html', context)
                username = form.cleaned_data.get('username')
                raw_password = form.cleaned_data.get('password1')
                user = authenticate(username=username, password=raw_password)
                current_site = get_current_site(request)
                print('after site:', current_site, current_site.domain)
                message = render_to_string('acc_active_email.html', {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': account_activation_token.make_token(user),
                    'protocol': 'https' if request.is_secure() else 'http',
                })
                # Sending activation link in terminal
                # user.email_user(subject, message)
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
                # send_mail(
                #     mail_subject,
                #     message,
                #     EMAIL_HOST_USER,
                #     [to_email],
                # )
                print('after send')
                # login(request, user)
                # return redirect('home')
                return render(request, 'acc_active_sent.html', {'form': form})
        else:
            form = SignupForm()
        context = {'form': form}
        return render(request, 'signup.html', context)
        # return send_http_response(status=HttpStatusCode['SERVER_ERROR'], err_msg=HttpErrorMsg['SERVER_ERROR'])

    except Exception as e:
        print(f'Exception occurred due to: {e}')
        return render(request, 'home.html')


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        users = User.objects.all()
        print(users)
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return send_http_response(data='Thank you for your email confirmation. Now you can login your account.')
    else:
        return send_http_response(data='Activation link is invalid!')


# class UserLoginView(View):
#     def post(self, *args, **kwargs):
class CustomLoginView(LoginView):
    form_class = LoginForm

    def form_valid(self, form):
        remember_me = form.cleaned_data.get('remember_me')

        if not remember_me:
            # set session expiry to 0 seconds. So it will automatically close the session after the browser is closed.
            self.request.session.set_expiry(0)

            # Set session as modified to force data updates/cookie to be saved.
            self.request.session.modified = True

        # else browser session will be as long as the session cookie time "SESSION_COOKIE_AGE" defined in settings.py
        return super(CustomLoginView, self).form_valid(form)
