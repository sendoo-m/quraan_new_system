from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_GENERAL_MANAGER = 'general_manager'
    ROLE_GENERAL_SUPERVISOR = 'general_supervisor'
    ROLE_HALL_SUPERVISOR = 'hall_supervisor'
    ROLE_TEACHER = 'teacher'
    ROLE_PARENT = 'parent'

    ROLES = [
        (ROLE_GENERAL_MANAGER, 'مدير عام'),
        (ROLE_GENERAL_SUPERVISOR, 'مشرف عام'),
        (ROLE_HALL_SUPERVISOR, 'مشرف قاعات'),
        (ROLE_TEACHER, 'معلم'),
        (ROLE_PARENT, 'ولي أمر'),
    ]

    role = models.CharField(
        max_length=30,
        choices=ROLES,
        default=ROLE_PARENT,
        verbose_name='الدور الوظيفي'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='رقم الهاتف'
    )
    profile_picture = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True,
        verbose_name='الصورة الشخصية'
    )

    # Helper Properties للصلاحيات
    @property
    def is_general_manager(self):
        return self.role == self.ROLE_GENERAL_MANAGER

    @property
    def is_general_supervisor(self):
        return self.role == self.ROLE_GENERAL_SUPERVISOR

    @property
    def is_hall_supervisor(self):
        return self.role == self.ROLE_HALL_SUPERVISOR

    @property
    def is_teacher(self):
        return self.role == self.ROLE_TEACHER

    @property
    def is_parent(self):
        return self.role == self.ROLE_PARENT

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    class Meta:
        verbose_name = 'مستخدم'
        verbose_name_plural = 'المستخدمون'

class SiteSettings(models.Model):
    """إعدادات المقرأة — سجل واحد فقط"""
    # بيانات المقرأة
    name         = models.CharField(max_length=200, default='مقرأة القرآن الكريم', verbose_name='اسم المقرأة')
    logo         = models.ImageField(upload_to='settings/', blank=True, null=True, verbose_name='الشعار')
    address      = models.CharField(max_length=300, blank=True, verbose_name='العنوان')
    phone        = models.CharField(max_length=20, blank=True, verbose_name='الهاتف')
    email        = models.EmailField(blank=True, verbose_name='البريد الإلكتروني')
    description  = models.TextField(blank=True, verbose_name='نبذة عن المقرأة')

    # إعدادات التسجيل
    allow_registration     = models.BooleanField(default=True, verbose_name='السماح بالتسجيل')
    auto_assign_halls      = models.BooleanField(default=True, verbose_name='التسكين التلقائي')
    max_age_limit          = models.PositiveIntegerField(default=15, verbose_name='الحد الأقصى للسن')
    min_age_limit          = models.PositiveIntegerField(default=3, verbose_name='الحد الأدنى للسن')

    # إعدادات الحضور
    attendance_start_time  = models.TimeField(default='08:00', verbose_name='وقت بداية الحضور')
    late_threshold_minutes = models.PositiveIntegerField(default=15, verbose_name='دقائق التأخير')

    # تواصل اجتماعي
    facebook    = models.URLField(blank=True, verbose_name='فيسبوك')
    whatsapp    = models.CharField(max_length=20, blank=True, verbose_name='واتساب')

    updated_at  = models.DateTimeField(auto_now=True)
    updated_by  = models.ForeignKey(
                      User,
                      on_delete=models.SET_NULL,
                      null=True, blank=True,
                      verbose_name='آخر تعديل بواسطة'
                  )

    def save(self, *args, **kwargs):
        self.pk = 1  # سجل واحد دايماً
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return self.name

    class Meta:
        verbose_name        = 'إعدادات الموقع'
        verbose_name_plural = 'إعدادات الموقع'
