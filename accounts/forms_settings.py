from django import forms
from .models import User, SiteSettings
from students.models import AgeGroup


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model  = SiteSettings
        fields = [
            'name', 'logo', 'address', 'phone', 'email', 'description',
            'allow_registration', 'auto_assign_halls',
            'min_age_limit', 'max_age_limit',
            'attendance_start_time', 'late_threshold_minutes',
            'facebook', 'whatsapp',
        ]
        widgets = {
            'name':                   forms.TextInput(attrs={'class': 'form-control'}),
            'logo':                   forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'address':                forms.TextInput(attrs={'class': 'form-control'}),
            'phone':                  forms.TextInput(attrs={'class': 'form-control'}),
            'email':                  forms.EmailInput(attrs={'class': 'form-control'}),
            'description':            forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'allow_registration':     forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'auto_assign_halls':      forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'min_age_limit':          forms.NumberInput(attrs={'class': 'form-control'}),
            'max_age_limit':          forms.NumberInput(attrs={'class': 'form-control'}),
            'attendance_start_time':  forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'late_threshold_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'facebook':               forms.URLInput(attrs={'class': 'form-control'}),
            'whatsapp':               forms.TextInput(attrs={'class': 'form-control'}),
        }


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='كلمة المرور',
        initial='Pass@1234'
    )
    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'username', 'email', 'phone', 'role', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control'}),
            'username':   forms.TextInput(attrs={'class': 'form-control'}),
            'email':      forms.EmailInput(attrs={'class': 'form-control'}),
            'phone':      forms.TextInput(attrs={'class': 'form-control'}),
            'role':       forms.Select(attrs={'class': 'form-select'},
                              choices=User.ROLES),   # ✅ ROLES مش ROLE_CHOICES
            'is_active':  forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'username', 'email', 'phone', 'role', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control'}),
            'username':   forms.TextInput(attrs={'class': 'form-control'}),
            'email':      forms.EmailInput(attrs={'class': 'form-control'}),
            'phone':      forms.TextInput(attrs={'class': 'form-control'}),
            'role':       forms.Select(attrs={'class': 'form-select'}),
            'is_active':  forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AgeGroupForm(forms.ModelForm):
    class Meta:
        model  = AgeGroup
        fields = ['name', 'min_age', 'max_age', 'order', 'is_active']
        widgets = {
            'name':      forms.TextInput(attrs={'class': 'form-control'}),
            'min_age':   forms.NumberInput(attrs={'class': 'form-control'}),
            'max_age':   forms.NumberInput(attrs={'class': 'form-control'}),
            'order':     forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name':      'اسم الفئة',
            'min_age':   'السن الأدنى',
            'max_age':   'السن الأقصى',
            'order':     'الترتيب',
            'is_active': 'نشطة',
        }
