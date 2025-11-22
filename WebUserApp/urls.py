from django.urls import path
from . import views

urlpatterns = [

    path('', views.home, name='user_home'),
    path('register/', views.register_view, name='user_register'),
    path('login/', views.login_user, name='login_user'),
    path('logout/', views.logout_user, name='logout_user'),
    path('profile/', views.user_profile, name='user_profile'),

  


]
