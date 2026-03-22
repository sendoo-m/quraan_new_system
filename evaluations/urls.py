from django.urls import path
from . import views

app_name = 'evaluations'

urlpatterns = [
    path('followup/add/',          views.AddFollowUpView.as_view(),       name='add_followup'),
    path('followup/<int:hall_id>/', views.HallFollowUpListView.as_view(), name='hall_followups'),
    path('evaluate/<int:student_id>/', views.EvaluateStudentView.as_view(), name='evaluate'),
    path('evaluate/hall/<int:hall_id>/', views.EvaluateHallView.as_view(), name='evaluate_hall'),
]
