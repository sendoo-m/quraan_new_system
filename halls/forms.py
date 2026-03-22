from django import forms
from .models import Hall, Subject, HallSchedule   # ← Subject مضافة هنا
from accounts.models import User
from students.models import AgeGroup


class HallForm(forms.ModelForm):
    class Meta:
        model  = Hall
        fields = [
            'name', 'location', 'age_group',
            'max_students', 'teacher', 'supervisor', 'is_active'
        ]
        widgets = {
            'name':         forms.TextInput(attrs={'class': 'form-control'}),
            'location':     forms.TextInput(attrs={'class': 'form-control'}),
            'age_group':    forms.Select(attrs={'class': 'form-select'}),
            'max_students': forms.NumberInput(attrs={'class': 'form-control'}),
            'teacher':      forms.Select(attrs={'class': 'form-select'}),
            'supervisor':   forms.Select(attrs={'class': 'form-select'}),
            'is_active':    forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name':         'اسم القاعة',
            'location':     'الموقع',
            'age_group':    'الفئة العمرية',
            'max_students': 'أقصى عدد للطلاب',
            'teacher':      'المعلم',
            'supervisor':   'مشرف القاعة',
            'is_active':    'نشطة',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['age_group'].queryset    = AgeGroup.objects.filter(is_active=True)
        self.fields['age_group'].empty_label  = '— اختر الفئة العمرية —'
        self.fields['teacher'].queryset      = User.objects.filter(role='teacher', is_active=True)
        self.fields['supervisor'].queryset   = User.objects.filter(role='hall_supervisor', is_active=True)
        self.fields['teacher'].empty_label    = '— اختر المعلم —'
        self.fields['supervisor'].empty_label = '— اختر المشرف —'


class HallScheduleForm(forms.ModelForm):
    class Meta:
        model  = HallSchedule
        fields = ['subject', 'day', 'start_time', 'end_time']
        widgets = {
            'subject':    forms.Select(attrs={'class': 'form-select'}),
            'day':        forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time':   forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }
        labels = {
            'subject':    'المادة',
            'day':        'اليوم',
            'start_time': 'وقت البداية',
            'end_time':   'وقت النهاية',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subject'].queryset      = Subject.objects.filter(is_active=True)
        self.fields['subject'].empty_label    = '— اختر المادة —'


class SubjectForm(forms.ModelForm):
    class Meta:
        model  = Subject
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name':        forms.TextInput(attrs={
                               'class': 'form-control',
                               'placeholder': 'اسم المادة'
                           }),
            'description': forms.Textarea(attrs={
                               'class': 'form-control',
                               'rows': 3,
                               'placeholder': 'وصف المادة (اختياري)'
                           }),
            'is_active':   forms.CheckboxInput(attrs={
                               'class': 'form-check-input'
                           }),
        }
        labels = {
            'name':        'اسم المادة',
            'description': 'وصف المادة',
            'is_active':   'نشطة',
        }
