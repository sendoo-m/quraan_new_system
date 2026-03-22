from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # حضور الطلاب
    path('students/',                views.StudentAttendanceView.as_view(), name='students'),
    path('students/<int:hall_id>/',  views.TakeAttendanceView.as_view(),   name='take'),
    path('report/',                  views.AttendanceReportView.as_view(), name='report'),

    # حضور الموظفين
    path('staff/',                   views.StaffAttendanceView.as_view(),       name='staff'),
    path('staff/mark/',              views.StaffAttendanceMarkView.as_view(),   name='staff_mark'),
    path('staff/report/',            views.StaffAttendanceReportView.as_view(), name='staff_report'),
]

# from django.urls import path
# from . import views

# app_name = 'attendance'

# urlpatterns = [
#     path('students/',           views.StudentAttendanceView.as_view(),  name='students'),
#     path('students/<int:hall_id>/', views.TakeAttendanceView.as_view(), name='take'),
#     path('staff/',              views.StaffAttendanceView.as_view(),    name='staff'),
#     path('report/',             views.AttendanceReportView.as_view(),   name='report'),
# ]
