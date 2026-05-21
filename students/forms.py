from django import forms
from .models import Student
from quran.models import Surah
from accounts.models import User, SiteSettings


class StudentRegistrationForm(forms.ModelForm):
    memorized_surahs = forms.ModelMultipleChoiceField(
        queryset=Surah.objects.all().order_by('number'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='السور المحفوظة'
    )

    class Meta:
        model  = Student
        fields = [
            'first_name', 'last_name', 'date_of_birth',
            'emergency_phone', 'memorized_surahs',
            'uses_bus', 'bus_notes', 'notes',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'الاسم الأول'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'اسم الرباعي'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'emergency_phone': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'رقم موبايل الطوارئ'
            }),
            'bus_notes': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'ملاحظات الباص'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3, 'placeholder': 'ملاحظات إضافية'
            }),
            'uses_bus': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'first_name':      'الاسم الأول',
            'last_name':       'اسم الرباعي',
            'date_of_birth':   'تاريخ الميلاد',
            'emergency_phone': 'رقم موبايل الطوارئ',
            'uses_bus':        'الاشتراك في خدمة الباص',
            'bus_notes':       'ملاحظات الباص',
            'notes':           'ملاحظات',
        }

    def __init__(self, *args, parent=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._parent = parent  # ← نمرر ولي الأمر للـ validation

    def clean_date_of_birth(self):
        from datetime import date
        dob   = self.cleaned_data.get('date_of_birth')
        today = date.today()
        age   = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        settings = SiteSettings.get_settings()
        if age < settings.min_age_limit or age > settings.max_age_limit:
            raise forms.ValidationError(
                f'عمر الطالب يجب أن يكون بين {settings.min_age_limit} '
                f'و {settings.max_age_limit} سنة'
            )
        return dob

    def clean(self):
        cleaned    = super().clean()
        uses_bus   = cleaned.get('uses_bus')
        bus_notes  = cleaned.get('bus_notes')
        first_name = cleaned.get('first_name', '').strip()
        last_name  = cleaned.get('last_name', '').strip()

        if not uses_bus:
            cleaned['bus_notes'] = ''
        if uses_bus and not bus_notes:
            self.add_error('bus_notes', 'اكتب ملاحظات الباص أو اترك الاشتراك غير مفعل')

        # ← جديد: منع تكرار اسم الطالب لنفس ولي الأمر
        if self._parent and first_name and last_name:
            exists = Student.objects.filter(
                parent=self._parent,
                first_name__iexact=first_name,
                last_name__iexact=last_name,
            ).exists()
            if exists:
                raise forms.ValidationError(
                    f'الطالب "{first_name} {last_name}" مسجل بالفعل في حسابك'
                )

        return cleaned


class TransferStudentForm(forms.Form):
    new_hall = forms.ModelChoiceField(
        queryset=None,
        label='القاعة الجديدة',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    reason = forms.CharField(
        label='سبب النقل',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2
        }),
        required=False
    )

    def __init__(self, student, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from halls.models import Hall
        self.student = student
        self.fields['new_hall'].queryset = Hall.objects.filter(
            age_group=student.age_group,
            is_active=True
        ).exclude(pk=student.hall_id)

    def clean_new_hall(self):
        hall = self.cleaned_data.get('new_hall')
        accepted, reason = hall.accepts_student(self.student)
        if not accepted:
            raise forms.ValidationError(reason)
        return hall


class StudentUpdateForm(forms.ModelForm):
    class Meta:
        model  = Student
        fields = [
            'first_name',
            'last_name',
            'date_of_birth',
            'emergency_phone',
            'memorized_surahs',
            'uses_bus',
            'bus_notes',
            'status',
            'notes',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d'
            ),
            'emergency_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'memorized_surahs': forms.CheckboxSelectMultiple(),
            'uses_bus':   forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'bus_notes':  forms.TextInput(attrs={'class': 'form-control'}),
            'status':     forms.Select(attrs={'class': 'form-select'}),
            'notes':      forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'first_name':      'الاسم الأول',
            'last_name':       'اسم الرباعي',
            'date_of_birth':   'تاريخ الميلاد',
            'emergency_phone': 'رقم موبايل الطوارئ',
            'memorized_surahs': 'السور المحفوظة',
            'uses_bus':        'يشترك في الباص',
            'bus_notes':       'ملاحظات الباص',
            'status':          'الحالة',
            'notes':           'ملاحظات عامة',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date_of_birth'].input_formats = ['%Y-%m-%d']
        self.fields['memorized_surahs'].queryset   = Surah.objects.all().order_by('number')

    def clean(self):
        cleaned   = super().clean()
        uses_bus  = cleaned.get('uses_bus')
        bus_notes = cleaned.get('bus_notes')

        if not uses_bus:
            cleaned['bus_notes'] = ''

        if uses_bus and not bus_notes:
            self.add_error('bus_notes', 'اكتب ملاحظات الباص أو ألغِ الاشتراك')

        return cleaned

class ParentRegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 'placeholder': 'كلمة المرور'
        }),
        label='كلمة المرور'
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 'placeholder': 'تأكيد كلمة المرور'
        }),
        label='تأكيد كلمة المرور'
    )

    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'username', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'الاسم الأول'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'اسم الرباعي'
            }),
            'username': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'اسم المستخدم'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': '05xxxxxxxx'
            }),
        }
        labels = {
            'first_name': 'اسم ولي الأمر',
            'last_name':  'اسم الرباعي',
            'username':   'اسم المستخدم',
            'phone':      'رقم الهاتف',
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('اسم المستخدم مستخدم بالفعل')
        return username

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if not phone:
            return None
        # ← جديد: تحقق من عدم تكرار رقم الهاتف
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError('رقم الهاتف مسجل بالفعل لحساب آخر')
        return phone

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password')
        p2 = cleaned.get('password_confirm')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('كلمتا المرور غير متطابقتين')
        return cleaned
    

class ParentStudentUpdateForm(forms.ModelForm):
    """فورم تعديل بيانات الطالب من جهة ولي الأمر — بدون حالة أو قاعة"""
    memorized_surahs = forms.ModelMultipleChoiceField(
        queryset=Surah.objects.all().order_by('number'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='السور المحفوظة'
    )

    class Meta:
        model  = Student
        fields = [
            'first_name', 'last_name', 'date_of_birth',
            'emergency_phone', 'memorized_surahs',
            'uses_bus', 'bus_notes', 'notes',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'الاسم الأول'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'اسم الرباعي'
            }),
            'date_of_birth': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d'
            ),
            'emergency_phone': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': '05xxxxxxxx'
            }),
            'bus_notes': forms.TextInput(attrs={'class': 'form-control'}),
            'notes':     forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'uses_bus':  forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'first_name':      'الاسم الأول',
            'last_name':       'اسم الرباعي',
            'date_of_birth':   'تاريخ الميلاد',
            'emergency_phone': 'رقم موبايل الطوارئ',
            'uses_bus':        'يشترك في الباص',
            'bus_notes':       'ملاحظات الباص',
            'notes':           'ملاحظات عامة',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date_of_birth'].input_formats = ['%Y-%m-%d']

    def clean(self):
        cleaned   = super().clean()
        uses_bus  = cleaned.get('uses_bus')
        bus_notes = cleaned.get('bus_notes')
        if not uses_bus:
            cleaned['bus_notes'] = ''
        if uses_bus and not bus_notes:
            self.add_error('bus_notes', 'اكتب ملاحظات الباص أو ألغِ الاشتراك')
        return cleaned
