from django import forms
from .models import StudentEvaluation, DailyFollowUp


class StudentEvaluationForm(forms.ModelForm):
    class Meta:
        model = StudentEvaluation
        fields = [
            'memorization_rating',
            'memorization_notes',
            'behavior_rating',
            'commitment_rating',
            'behavior_notes',
            'is_distinguished',
            'needs_attention',
            'general_notes',
        ]
        widgets = {
            'memorization_rating': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'behavior_rating':     forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'commitment_rating':   forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'memorization_notes':  forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 2}),
            'behavior_notes':      forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 2}),
            'general_notes':       forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 2}),
            'is_distinguished':    forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'needs_attention':     forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class DailyFollowUpForm(forms.ModelForm):
    class Meta:
        model = DailyFollowUp
        fields = ['homework', 'memorization_task', 'extra_notes']
        widgets = {
            'homework':          forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'memorization_task': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'extra_notes':       forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }