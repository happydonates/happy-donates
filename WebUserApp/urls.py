from django.urls import path
from . import views

urlpatterns = [

    path('', views.home, name='user_home'),
    path('register/', views.register_view, name='user_register'),
    path('login/', views.login_user, name='login_user'),
    path('logout/', views.logout_user, name='logout_user'),
    path('profile/', views.user_profile, name='user_profile'),
    path('browse_items/', views.browse_items, name='browse_items'),
    path('item/<str:slug>/', views.single_item_view, name='item_detail'),
    path('donations/', views.donation_list, name='donation_list'),
    path('donation-detail/<str:slug>/', views.donation_detail, name='donation_detail'),
    path('donate-item/', views.donate_item, name='donate_item'),
    path('edit-donate-item/<str:slug>/', views.edit_donate_item, name='edit_donate_item'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/delete/', views.delete_account, name='delete_account'),
    path('profile/<str:username>/', views.public_profile_view, name='public_profile'),

  


]
