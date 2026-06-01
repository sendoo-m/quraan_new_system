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


    # ══ الجداول النموذجية ══
    path('schedule-templates/',
         views.ScheduleTemplateListView.as_view(),       name='templates'),
    path('schedule-templates/create/',
         views.ScheduleTemplateCreateView.as_view(),     name='template_create'),
    path('schedule-templates/<int:pk>/',
         views.ScheduleTemplateDetailView.as_view(),     name='template_detail'),
    path('schedule-templates/<int:pk>/update/',
         views.ScheduleTemplateUpdateView.as_view(),     name='template_update'),
    path('schedule-templates/<int:pk>/delete/',
         views.ScheduleTemplateDeleteView.as_view(),     name='template_delete'),
    path('schedule-templates/<int:pk>/entry/add/',
         views.TemplateEntryAddView.as_view(),           name='template_entry_add'),
    path('schedule-templates/entry/<int:entry_pk>/delete/',
         views.TemplateEntryDeleteView.as_view(),        name='template_entry_delete'),
    path('schedule-templates/<int:pk>/assign-halls/',
         views.TemplateAssignHallsView.as_view(), name='template_assign_halls'),
    path('<int:pk>/export-excel/', views.HallExportExcelView.as_view(), name='export_excel'),
]
