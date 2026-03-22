from django.urls import path
from . import views_settings as views

app_name = 'settings'

urlpatterns = [
    # الرئيسية
    path('',                              views.SettingsHomeView.as_view(),      name='home'),
    path('site/',                         views.SiteSettingsView.as_view(),      name='site'),

    # المستخدمون
    path('users/',                        views.UsersManageView.as_view(),       name='users'),
    path('users/create/',                 views.UserCreateView.as_view(),        name='user_create'),
    path('users/<int:pk>/update/',        views.UserUpdateView.as_view(),        name='user_update'),
    path('users/<int:pk>/toggle/',        views.UserToggleActiveView.as_view(),  name='user_toggle'),
    path('users/<int:pk>/reset-password/', views.UserResetPasswordView.as_view(), name='user_reset_password'),

    # الفئات العمرية
    path('age-groups/',                   views.AgeGroupsView.as_view(),        name='age_groups'),
    path('age-groups/create/',            views.AgeGroupCreateView.as_view(),   name='age_group_create'),
    path('age-groups/<int:pk>/update/',   views.AgeGroupUpdateView.as_view(),   name='age_group_update'),
    path('age-groups/<int:pk>/delete/',   views.AgeGroupDeleteView.as_view(),   name='age_group_delete'),
]
