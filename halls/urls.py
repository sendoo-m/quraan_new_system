from django.urls import path
from . import views

app_name = 'halls'

urlpatterns = [
    path('',                    views.HallListView.as_view(),      name='list'),
    path('create/',             views.HallCreateView.as_view(),    name='create'),
    path('<int:pk>/',           views.HallDetailView.as_view(),    name='detail'),
    path('<int:pk>/schedule/',  views.HallScheduleView.as_view(),  name='schedule'),
    path('all-schedules/',      views.AllSchedulesView.as_view(),  name='all_schedules'),  # ✅ جديد
    path('<int:pk>/update/',    views.HallUpdateView.as_view(), name='update'),

    # المواد الدراسية ✅
    path('subjects/',                views.SubjectListView.as_view(),    name='subjects'),
    path('subjects/create/',         views.SubjectCreateView.as_view(),  name='subject_create'),
    path('subjects/<int:pk>/update/', views.SubjectUpdateView.as_view(), name='subject_update'),
    path('subjects/<int:pk>/delete/', views.SubjectDeleteView.as_view(), name='subject_delete'),

]
