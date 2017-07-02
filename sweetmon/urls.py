"""sweetmon URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, views

# DEPRECATED
# from monitor.views import ShowProfile, ModifyProfile

urlpatterns = [
	url(r'^$',include('monitor.urls'), name='index'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^monitor/', include('monitor.urls')),
    url(r'^fuzz/', include('fuzz.urls')),
    url(r'^testcase/', include('testcase.urls')),
    url(r'^track/', include('track.urls')),
    url(r'^account/login/',auth_views.login,name='login',kwargs={'template_name': 'login.html'}),
    url(r'^account/logout/',auth_views.logout,name='logout',kwargs={'next_page': settings.LOGIN_URL,}),

    # DEPRECATED
    # url(r'^account/profile/$',ShowProfile, name="profile"),
    # url(r'^account/profile/modify$',ModifyProfile, name="profile"),
]
