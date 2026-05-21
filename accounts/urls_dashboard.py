from django.urls import path
from . import views_dashboard

app_name = 'dashboard'

urlpatterns = [
    path('manager/',         views_dashboard.ManagerDashboard.as_view(),           name='manager'),
    path('supervisor/',      views_dashboard.GeneralSupervisorDashboard.as_view(), name='supervisor'),
    path('hall-supervisor/', views_dashboard.HallSupervisorDashboard.as_view(),    name='hall_supervisor'),
    path('teacher/',         views_dashboard.TeacherDashboard.as_view(),           name='teacher'),
    path('parent/',          views_dashboard.ParentDashboard.as_view(),            name='parent'),
    path('parent/report/<int:student_id>/',
                             views_dashboard.ParentStudentReportView.as_view(),    name='student_report'),
    path('parent/profile/',  views_dashboard.ParentProfileView.as_view(),          name='parent_profile'),
    # ← جديد
    path('parent/child/<int:student_id>/edit/',
                             views_dashboard.ParentStudentUpdateView.as_view(),    name='parent_student_edit'),
]
