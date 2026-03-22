from django.urls import path
from . import views, views_dashboard

app_name = 'accounts'

urlpatterns = [
    path('login/',    views.LoginView.as_view(),    name='login'),
    path('logout/',   views.LogoutView.as_view(),   name='logout'),
    path('',          views.DashboardView.as_view(), name='dashboard_redirect'),
]
