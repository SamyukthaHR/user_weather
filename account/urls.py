from django.urls import path

from account import views as account_views
from django.contrib.auth import views as auth_views

from account.forms import LoginForm
from account.views import CustomLoginView, UserSignUpView, WeatherDetailsView

urlpatterns = [
    path('signup', UserSignUpView.as_view(), name='signup'),
    path('activate/<uidb64>/<token>', account_views.activate, name='activate'),
    path('', account_views.home, name='home'),
    path('logout', auth_views.LogoutView.as_view(template_name="logout.html"), name='logout'),
    path('login/', CustomLoginView.as_view(redirect_authenticated_user=True, template_name='login.html',
                                           authentication_form=LoginForm), name='login'),
    path('profile/', account_views.profile, name='profile'),
    path('weather', WeatherDetailsView.as_view()),
]
