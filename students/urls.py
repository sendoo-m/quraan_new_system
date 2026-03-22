from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('',                      views.StudentListView.as_view(),    name='list'),
    path('register/',             views.StudentRegisterView.as_view(),name='register'),
    path('<int:pk>/',             views.StudentDetailView.as_view(),  name='detail'),
    path('<int:pk>/update/',        views.StudentUpdateView.as_view(),   name='update'),   # ← جديد
    path('<int:pk>/assign-hall/', views.AssignHallView.as_view(),     name='assign_hall'),
    path('<int:pk>/transfer/',    views.TransferStudentView.as_view(),name='transfer'),

]
