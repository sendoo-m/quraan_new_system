from django.contrib import admin
from .models import DailyFollowUp, StudentEvaluation


@admin.register(DailyFollowUp)
class DailyFollowUpAdmin(admin.ModelAdmin):
    list_display  = ('hall', 'date', 'created_by', 'created_at')
    list_filter   = ('hall', 'date')
    date_hierarchy = 'date'


@admin.register(StudentEvaluation)
class StudentEvaluationAdmin(admin.ModelAdmin):
    list_display  = (
        'student', 'date', 'memorization_rating',
        'behavior_rating', 'commitment_rating',
        'is_distinguished', 'needs_attention', 'teacher'
    )
    list_filter   = ('memorization_rating', 'behavior_rating', 'is_distinguished', 'needs_attention')
    search_fields = ('student__first_name', 'student__last_name')
    date_hierarchy = 'date'
