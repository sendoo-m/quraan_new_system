"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from students.views import PublicRegisterView
from accounts.views import DashboardView

urlpatterns = [
    path('',           PublicRegisterView.as_view(), name='home'),
    path('admin/',     admin.site.urls),
    path('dashboard',  DashboardView.as_view(),      name='dashboard'),  # ← redirect view
    path('accounts/',  include('accounts.urls',             namespace='accounts')),
    path('dashboard/', include('accounts.urls_dashboard',   namespace='dashboard')),
    path('students/',  include('students.urls',             namespace='students')),
    path('halls/',     include('halls.urls',                namespace='halls')),
    path('attendance/',include('attendance.urls',           namespace='attendance')),
    path('evaluations/',include('evaluations.urls',         namespace='evaluations')),
    path('settings/',  include('accounts.urls_settings',    namespace='settings')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
