from django import forms
from .models import User, SiteSettings
from students.models import AgeGroup


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            'name', 'logo', 'address', 'phone', 'email', 'description',
            'allow_registration', 'auto_assign_halls',
            'min_age_limit', 'max_age_limit',
            'attendance_start_time', 'late_threshold_minutes',
            'facebook', 'whatsapp',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'allow_registration': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'auto_assign_halls': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'min_age_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_age_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'attendance_start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'late_threshold_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'facebook': forms.URLInput(attrs={'class': 'form-control'}),
            'whatsapp': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned = super().clean()
        min_age = cleaned.get('min_age_limit')
        max_age = cleaned.get('max_age_limit')
        if min_age is not None and max_age is not None and min_age > max_age:
            raise forms.ValidationError('الحد الأدنى للسن يجب أن يكون أقل من أو يساوي الحد الأقصى')
        return cleaned


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='كلمة المرور'
    )

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'username', 'email', 'phone', 'role', 'is_active',
            'can_manage_users', 'can_manage_halls', 'can_manage_students',
            'can_manage_attendance', 'can_manage_evaluations', 'can_manage_settings',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_users': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_halls': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_students': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_attendance': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_evaluations': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_settings': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'first_name': 'الاسم الأول',
            'last_name': 'اسم العائلة',
            'username': 'اسم المستخدم',
            'email': 'البريد الإلكتروني',
            'phone': 'رقم الهاتف',
            'role': 'الدور الوظيفي',
            'is_active': 'نشط',
            'can_manage_users': 'إدارة المستخدمين',
            'can_manage_halls': 'إدارة القاعات',
            'can_manage_students': 'إدارة الطلاب',
            'can_manage_attendance': 'إدارة الحضور',
            'can_manage_evaluations': 'إدارة التقييمات',
            'can_manage_settings': 'إدارة الإعدادات',
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('اسم المستخدم مستخدم بالفعل')
        return username

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get('role')

        if role == User.ROLE_PARENT:
            cleaned['can_manage_users'] = False
            cleaned['can_manage_halls'] = False
            cleaned['can_manage_students'] = False
            cleaned['can_manage_attendance'] = False
            cleaned['can_manage_evaluations'] = False
            cleaned['can_manage_settings'] = False

        if role == User.ROLE_GENERAL_MANAGER:
            cleaned['can_manage_users'] = True
            cleaned['can_manage_halls'] = True
            cleaned['can_manage_students'] = True
            cleaned['can_manage_attendance'] = True
            cleaned['can_manage_evaluations'] = True
            cleaned['can_manage_settings'] = True

        return cleaned


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'username', 'email', 'phone', 'role', 'is_active',
            'can_manage_users', 'can_manage_halls', 'can_manage_students',
            'can_manage_attendance', 'can_manage_evaluations', 'can_manage_settings',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_users': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_halls': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_students': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_attendance': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_evaluations': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_settings': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'first_name': 'الاسم الأول',
            'last_name': 'اسم العائلة',
            'username': 'اسم المستخدم',
            'email': 'البريد الإلكتروني',
            'phone': 'رقم الهاتف',
            'role': 'الدور الوظيفي',
            'is_active': 'نشط',
            'can_manage_users': 'إدارة المستخدمين',
            'can_manage_halls': 'إدارة القاعات',
            'can_manage_students': 'إدارة الطلاب',
            'can_manage_attendance': 'إدارة الحضور',
            'can_manage_evaluations': 'إدارة التقييمات',
            'can_manage_settings': 'إدارة الإعدادات',
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        qs = User.objects.filter(username=username)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('اسم المستخدم مستخدم بالفعل')
        return username

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get('role')

        if role == User.ROLE_PARENT:
            cleaned['can_manage_users'] = False
            cleaned['can_manage_halls'] = False
            cleaned['can_manage_students'] = False
            cleaned['can_manage_attendance'] = False
            cleaned['can_manage_evaluations'] = False
            cleaned['can_manage_settings'] = False

        if role == User.ROLE_GENERAL_MANAGER:
            cleaned['can_manage_users'] = True
            cleaned['can_manage_halls'] = True
            cleaned['can_manage_students'] = True
            cleaned['can_manage_attendance'] = True
            cleaned['can_manage_evaluations'] = True
            cleaned['can_manage_settings'] = True

        return cleaned


class AgeGroupForm(forms.ModelForm):
    class Meta:
        model = AgeGroup
        fields = ['name', 'min_age', 'max_age', 'order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'min_age': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_age': forms.NumberInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': 'اسم الفئة',
            'min_age': 'السن الأدنى',
            'max_age': 'السن الأقصى',
            'order': 'الترتيب',
            'is_active': 'نشطة',
        }

    def clean(self):
        cleaned = super().clean()
        min_age = cleaned.get('min_age')
        max_age = cleaned.get('max_age')
        if min_age is not None and max_age is not None and min_age > max_age:
            raise forms.ValidationError('السن الأدنى يجب أن يكون أقل من أو يساوي السن الأقصى')
        return cleaned

# from django import forms
# from .models import User, SiteSettings
# from students.models import AgeGroup


# class SiteSettingsForm(forms.ModelForm):
#     class Meta:
#         model  = SiteSettings
#         fields = [
#             'name', 'logo', 'address', 'phone', 'email', 'description',
#             'allow_registration', 'auto_assign_halls',
#             'min_age_limit', 'max_age_limit',
#             'attendance_start_time', 'late_threshold_minutes',
#             'facebook', 'whatsapp',
#         ]
#         widgets = {
#             'name':                   forms.TextInput(attrs={'class': 'form-control'}),
#             'logo':                   forms.ClearableFileInput(attrs={'class': 'form-control'}),
#             'address':                forms.TextInput(attrs={'class': 'form-control'}),
#             'phone':                  forms.TextInput(attrs={'class': 'form-control'}),
#             'email':                  forms.EmailInput(attrs={'class': 'form-control'}),
#             'description':            forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
#             'allow_registration':     forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#             'auto_assign_halls':      forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#             'min_age_limit':          forms.NumberInput(attrs={'class': 'form-control'}),
#             'max_age_limit':          forms.NumberInput(attrs={'class': 'form-control'}),
#             'attendance_start_time':  forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
#             'late_threshold_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
#             'facebook':               forms.URLInput(attrs={'class': 'form-control'}),
#             'whatsapp':               forms.TextInput(attrs={'class': 'form-control'}),
#         }


# class UserCreateForm(forms.ModelForm):
#     password = forms.CharField(
#         widget=forms.PasswordInput(attrs={'class': 'form-control'}),
#         label='كلمة المرور',
#         initial='Pass@1234'
#     )
#     class Meta:
#         model  = User
#         fields = ['first_name', 'last_name', 'username', 'email', 'phone', 'role', 'is_active']
#         widgets = {
#             'first_name': forms.TextInput(attrs={'class': 'form-control'}),
#             'last_name':  forms.TextInput(attrs={'class': 'form-control'}),
#             'username':   forms.TextInput(attrs={'class': 'form-control'}),
#             'email':      forms.EmailInput(attrs={'class': 'form-control'}),
#             'phone':      forms.TextInput(attrs={'class': 'form-control'}),
#             'role':       forms.Select(attrs={'class': 'form-select'},
#                               choices=User.ROLES),   # ✅ ROLES مش ROLE_CHOICES
#             'is_active':  forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#         }

# class UserUpdateForm(forms.ModelForm):
#     class Meta:
#         model  = User
#         fields = ['first_name', 'last_name', 'username', 'email', 'phone', 'role', 'is_active']
#         widgets = {
#             'first_name': forms.TextInput(attrs={'class': 'form-control'}),
#             'last_name':  forms.TextInput(attrs={'class': 'form-control'}),
#             'username':   forms.TextInput(attrs={'class': 'form-control'}),
#             'email':      forms.EmailInput(attrs={'class': 'form-control'}),
#             'phone':      forms.TextInput(attrs={'class': 'form-control'}),
#             'role':       forms.Select(attrs={'class': 'form-select'}),
#             'is_active':  forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#         }


# class AgeGroupForm(forms.ModelForm):
#     class Meta:
#         model  = AgeGroup
#         fields = ['name', 'min_age', 'max_age', 'order', 'is_active']
#         widgets = {
#             'name':      forms.TextInput(attrs={'class': 'form-control'}),
#             'min_age':   forms.NumberInput(attrs={'class': 'form-control'}),
#             'max_age':   forms.NumberInput(attrs={'class': 'form-control'}),
#             'order':     forms.NumberInput(attrs={'class': 'form-control'}),
#             'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#         }
#         labels = {
#             'name':      'اسم الفئة',
#             'min_age':   'السن الأدنى',
#             'max_age':   'السن الأقصى',
#             'order':     'الترتيب',
#             'is_active': 'نشطة',
#         }
