"""
URL configuration for express project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from expressapp import views
from expressapp.views import Index, About, Register, LogOut, PickRide, RideCards, Rides, PubRide

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', Register.as_view(), name="register"),
    path('logIn/', views.logIn, name="logIn"),
    path('logOut/', LogOut.as_view(), name='logOut'),
    path('accounts/', include('allauth.urls')),
    path('', Index.as_view(), name='index'),
    path('about/', About.as_view(), name='about'),
    path('pickRide/', PickRide.as_view(), name='pickRide'),
    path('rides/', Rides.as_view(), name='rides'),
    path('PubRide/', PubRide.as_view(), name='PubRide'),
    path('rideCards/<int:pk>', RideCards.as_view(), name='rideCards'),
    path('activate/<uidb64>/<token>/', views.activate, name="activate"),
    path('yourRides/<int:pk>/', views.yourRides, name='yourRides'),
    path('riderInfo/<int:id>/', views.riderInfo, name='riderInfo'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('editProfile/', views.editProfile, name='editProfile'),
    path('booking/<int:pk>/', views.booking, name='booking'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)