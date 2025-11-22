from django.urls import path

from . import views

urlpatterns = [

    path('', views.home, name='user_home'),
    path('register/', views.register_view, name='user_register'),
    path('login/', views.login, name='login_user'),

  


]
