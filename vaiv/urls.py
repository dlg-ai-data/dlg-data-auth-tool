"""vaiv_backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
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
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from django.conf import settings
from vaiv.view import MainView

urlpatterns = [
    url(r'^member/', include('member.urls', namespace='member')),
    url(r'^board/', include('board.urls', namespace='board')),
    url(r'^calc/', include('calc.urls', namespace='calc')),
    url(r'^dataset/', include('dataset.urls', namespace='dataset')),
    url(r'^job/', include('job.urls', namespace='job')),
    url(r'^common/', include('common.urls', namespace='common')),
    url(r'^$', MainView.as_view(), name='main'),
    url(r'^logout/', auth_views.LogoutView.as_view(), name='logout'),
]
