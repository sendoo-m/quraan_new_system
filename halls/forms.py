from django import forms
from .models import Hall, Subject, HallSchedule
from accounts.models import User
from students.models import AgeGroup

class HallForm(forms.ModelForm):
    class Meta:
        model = Hall
        fields = [
            'name', 'location', 'age_group', 'max_students',
            'general_supervisor', 'teacher', 'supervisor',
            'current_juz', 'required_completed_juz_count', 'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'age_group': forms.Select(attrs={'class': 'form-select'}),
            'max_students': forms.NumberInput(attrs={'class': 'form-control'}),
            'general_supervisor': forms.Select(attrs={'class': 'form-select'}),
            'teacher': forms.Select(attrs={'class': 'form-select'}),
            'supervisor': forms.Select(attrs={'class': 'form-select'}),
            'current_juz': forms.NumberInput(attrs={'class': 'form-control'}),
            'required_completed_juz_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        self.fields['age_group'].queryset = AgeGroup.objects.filter(is_active=True)
        self.fields['age_group'].empty_label = '— اختر الفئة العمرية —'

        self.fields['general_supervisor'].queryset = User.objects.filter(
            role=User.ROLE_GENERAL_SUPERVISOR,
            is_active=True
        )
        self.fields['teacher'].queryset = User.objects.filter(
            role=User.ROLE_TEACHER,
            is_active=True
        )
        self.fields['supervisor'].queryset = User.objects.filter(
            role=User.ROLE_HALL_SUPERVISOR,
            is_active=True
        )

        if self.user and self.user.is_general_supervisor and not self.user.is_general_manager:
            self.fields['general_supervisor'].queryset = User.objects.filter(pk=self.user.pk)
            self.fields['general_supervisor'].initial = self.user

        self.fields['general_supervisor'].empty_label = '— اختر المشرف العام —'
        self.fields['teacher'].empty_label = '— اختر المعلم —'
        self.fields['supervisor'].empty_label = '— اختر المشرف —'

    def clean_current_juz(self):
        value = self.cleaned_data.get('current_juz')
        if value < 1 or value > 30:
            raise forms.ValidationError('رقم الجزء يجب أن يكون بين 1 و 30')
        return value

    def clean_required_completed_juz_count(self):
        value = self.cleaned_data.get('required_completed_juz_count')
        if value < 0 or value > 30:
            raise forms.ValidationError('عدد الأجزاء المطلوبة يجب أن يكون بين 0 و 30')
        return value

    def clean_max_students(self):
        value = self.cleaned_data.get('max_students')
        if value < 1:
            raise forms.ValidationError('أقصى عدد للطلاب يجب أن يكون أكبر من صفر')
        if self.instance and self.instance.pk:
            current_active = self.instance.students.filter(status='active').count()
            if value < current_active:
                raise forms.ValidationError(
                    f'لا يمكن جعل السعة أقل من عدد الطلاب النشطين الحالي ({current_active})'
                )
        return value

class HallScheduleForm(forms.ModelForm):
    class Meta:
        model = HallSchedule
        fields = ['subject', 'day', 'start_time', 'end_time']
        widgets = {
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'day': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }
        labels = {
            'subject': 'المادة',
            'day': 'اليوم',
            'start_time': 'وقت البداية',
            'end_time': 'وقت النهاية',
        }

    def __init__(self, *args, **kwargs):
        self.hall = kwargs.pop('hall', None)
        super().__init__(*args, **kwargs)
        self.fields['subject'].queryset = Subject.objects.filter(is_active=True)
        self.fields['subject'].empty_label = '— اختر المادة —'

    def clean(self):
        cleaned = super().clean()
        start_time = cleaned.get('start_time')
        end_time = cleaned.get('end_time')
        day = cleaned.get('day')

        if start_time and end_time and end_time <= start_time:
            raise forms.ValidationError('وقت النهاية يجب أن يكون بعد وقت البداية')

        if self.hall and day and start_time and end_time:
            qs = HallSchedule.objects.filter(hall=self.hall, day=day)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            for item in qs:
                overlap = start_time < item.end_time and end_time > item.start_time
                if overlap:
                    raise forms.ValidationError(
                        f'يوجد تعارض مع حصة أخرى من {item.start_time} إلى {item.end_time}'
                    )

        return cleaned


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم المادة'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'وصف المادة (اختياري)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'name': 'اسم المادة',
            'description': 'وصف المادة',
            'is_active': 'نشطة',
        }

        
# from django import forms
# from .models import Hall, Subject, HallSchedule   # ← Subject مضافة هنا
# from accounts.models import User
# from students.models import AgeGroup


# class HallForm(forms.ModelForm):
#     class Meta:
#         model  = Hall
#         fields = [
#             'name', 'location', 'age_group',
#             'max_students', 'teacher', 'supervisor', 'is_active'
#         ]
#         widgets = {
#             'name':         forms.TextInput(attrs={'class': 'form-control'}),
#             'location':     forms.TextInput(attrs={'class': 'form-control'}),
#             'age_group':    forms.Select(attrs={'class': 'form-select'}),
#             'max_students': forms.NumberInput(attrs={'class': 'form-control'}),
#             'teacher':      forms.Select(attrs={'class': 'form-select'}),
#             'supervisor':   forms.Select(attrs={'class': 'form-select'}),
#             'is_active':    forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#         }
#         labels = {
#             'name':         'اسم القاعة',
#             'location':     'الموقع',
#             'age_group':    'الفئة العمرية',
#             'max_students': 'أقصى عدد للطلاب',
#             'teacher':      'المعلم',
#             'supervisor':   'مشرف القاعة',
#             'is_active':    'نشطة',
#         }

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields['age_group'].queryset    = AgeGroup.objects.filter(is_active=True)
#         self.fields['age_group'].empty_label  = '— اختر الفئة العمرية —'
#         self.fields['teacher'].queryset      = User.objects.filter(role='teacher', is_active=True)
#         self.fields['supervisor'].queryset   = User.objects.filter(role='hall_supervisor', is_active=True)
#         self.fields['teacher'].empty_label    = '— اختر المعلم —'
#         self.fields['supervisor'].empty_label = '— اختر المشرف —'


# class HallScheduleForm(forms.ModelForm):
#     class Meta:
#         model  = HallSchedule
#         fields = ['subject', 'day', 'start_time', 'end_time']
#         widgets = {
#             'subject':    forms.Select(attrs={'class': 'form-select'}),
#             'day':        forms.Select(attrs={'class': 'form-select'}),
#             'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
#             'end_time':   forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
#         }
#         labels = {
#             'subject':    'المادة',
#             'day':        'اليوم',
#             'start_time': 'وقت البداية',
#             'end_time':   'وقت النهاية',
#         }

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields['subject'].queryset      = Subject.objects.filter(is_active=True)
#         self.fields['subject'].empty_label    = '— اختر المادة —'


# class SubjectForm(forms.ModelForm):
#     class Meta:
#         model  = Subject
#         fields = ['name', 'description', 'is_active']
#         widgets = {
#             'name':        forms.TextInput(attrs={
#                                'class': 'form-control',
#                                'placeholder': 'اسم المادة'
#                            }),
#             'description': forms.Textarea(attrs={
#                                'class': 'form-control',
#                                'rows': 3,
#                                'placeholder': 'وصف المادة (اختياري)'
#                            }),
#             'is_active':   forms.CheckboxInput(attrs={
#                                'class': 'form-check-input'
#                            }),
#         }
#         labels = {
#             'name':        'اسم المادة',
#             'description': 'وصف المادة',
#             'is_active':   'نشطة',
#         }
