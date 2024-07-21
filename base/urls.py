from django.urls import path
from . import views

urlpatterns = [
    path('home', views.home, name='home'),
    path('room/', views.room, name='room'),
    path('', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('result/', views.predict, name='predict_personality'),
    path('connect/', views.connect, name='connect'),
    path('personality-test/', views.personality_test, name='personality_test'),
    #path('logout/', views.logout, name='logout')
]