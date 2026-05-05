from django.urls import path, include
from .views import LoginView, LogoutView, DashboardView

app_name = 'accounts'

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),

    path('d/', include('accounts.urls_dashboard')),
    path('settings/', include('accounts.urls_settings')),
]
# from django.urls import path
# from . import views, views_dashboard

# app_name = 'accounts'

# urlpatterns = [
#     path('login/',    views.LoginView.as_view(),    name='login'),
#     path('logout/',   views.LogoutView.as_view(),   name='logout'),
#     path('',          views.DashboardView.as_view(), name='dashboard_redirect'),
# ]
