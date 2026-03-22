from django.urls import path
from . import views_dashboard

app_name = 'dashboard'

urlpatterns = [
    path('manager/',         views_dashboard.ManagerDashboard.as_view(),           name='manager'),
    path('supervisor/',      views_dashboard.GeneralSupervisorDashboard.as_view(), name='supervisor'),
    path('hall-supervisor/', views_dashboard.HallSupervisorDashboard.as_view(),    name='hall_supervisor'),
    path('teacher/',         views_dashboard.TeacherDashboard.as_view(),           name='teacher'),
    path('parent/',          views_dashboard.ParentDashboard.as_view(),            name='parent'),
]

# from django.urls import path
# from . import views, views_dashboard

# urlpatterns = [
#     path('', views.DashboardView.as_view(), name='dashboard'),
# ]

# dashboard_urls = ([
#     path('manager/',         views_dashboard.ManagerDashboard.as_view(),           name='manager'),
#     path('supervisor/',      views_dashboard.GeneralSupervisorDashboard.as_view(), name='supervisor'),
#     path('hall-supervisor/', views_dashboard.HallSupervisorDashboard.as_view(),    name='hall_supervisor'),
#     path('teacher/',         views_dashboard.TeacherDashboard.as_view(),           name='teacher'),
#     path('parent/',          views_dashboard.ParentDashboard.as_view(),            name='parent'),
# ], 'dashboard')

# from django.urls import include
# urlpatterns += [
#     path('dashboard/', include(dashboard_urls)),
# ]
