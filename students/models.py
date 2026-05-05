from django.db import models
from django.core.exceptions import ValidationError
from accounts.models import User
from quran.models import Surah


class AgeGroup(models.Model):
    name = models.CharField(max_length=100, verbose_name='اسم الفئة')
    min_age = models.PositiveIntegerField(verbose_name='الحد الأدنى للسن')
    max_age = models.PositiveIntegerField(verbose_name='الحد الأقصى للسن')
    order = models.PositiveIntegerField(default=0, verbose_name='الترتيب')
    is_active = models.BooleanField(default=True, verbose_name='نشطة')

    def clean(self):
        if self.min_age > self.max_age:
            raise ValidationError('الحد الأدنى يجب أن يكون أقل من أو يساوي الحد الأقصى')

    def __str__(self):
        return f"{self.name} ({self.min_age} - {self.max_age} سنة)"

    class Meta:
        verbose_name = 'فئة عمرية'
        verbose_name_plural = 'الفئات العمرية'
        ordering = ['order', 'min_age']


class Student(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'في انتظار التسكين'),
        (STATUS_ACTIVE, 'نشط'),
        (STATUS_INACTIVE, 'غير نشط'),
        (STATUS_REJECTED, 'مرفوض لعدم وجود قاعة مناسبة'),
    ]

    first_name = models.CharField(max_length=50, verbose_name='الاسم الأول')
    last_name = models.CharField(max_length=50, verbose_name='اسم العائلة')
    date_of_birth = models.DateField(verbose_name='تاريخ الميلاد')
    age_group = models.ForeignKey(
        'students.AgeGroup',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        verbose_name='الفئة العمرية'
    )
    profile_picture = models.ImageField(
        upload_to='students/',
        blank=True,
        null=True,
        verbose_name='صورة الطالب'
    )
    memorized_surahs = models.ManyToManyField(
        Surah,
        blank=True,
        verbose_name='السور المحفوظة',
        related_name='memorized_by'
    )

    parent = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='children',
        limit_choices_to={'role': 'parent'},
        verbose_name='ولي الأمر'
    )
    hall = models.ForeignKey(
        'halls.Hall',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        verbose_name='القاعة'
    )

    uses_bus = models.BooleanField(default=False, verbose_name='يشترك في الباص')
    bus_notes = models.CharField(max_length=200, blank=True, verbose_name='ملاحظات الباص')

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name='حالة الطالب'
    )
    registration_date = models.DateField(auto_now_add=True, verbose_name='تاريخ التسجيل')
    notes = models.TextField(blank=True, verbose_name='ملاحظات عامة')

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def calculate_age(self):
        from datetime import date
        today = date.today()
        born = self.date_of_birth
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    def get_matching_age_group(self):
        age = self.calculate_age()
        return AgeGroup.objects.filter(
            min_age__lte=age,
            max_age__gte=age,
            is_active=True
        ).order_by('order').first()

    def get_memorization_level(self):
        return self.memorized_surahs.count()

    def get_completed_juz_count(self):
        juzs = set(self.memorized_surahs.values_list('juz', flat=True))
        return len(juzs)

    def save(self, *args, **kwargs):
        matched = self.get_matching_age_group()
        if matched:
            self.age_group = matched
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_full_name()} ({self.calculate_age()} سنة)"

    class Meta:
        verbose_name = 'طالب'
        verbose_name_plural = 'الطلاب'
        ordering = ['first_name', 'last_name']


# from django.db import models
# from django.core.exceptions import ValidationError
# from accounts.models import User
# from quran.models import Surah


# class AgeGroup(models.Model):
#     """فئات عمرية ديناميكية — تُضاف وتُعدَّل من الإدارة"""
#     name      = models.CharField(max_length=100, verbose_name='اسم الفئة')
#     min_age   = models.PositiveIntegerField(verbose_name='الحد الأدنى للسن')
#     max_age   = models.PositiveIntegerField(verbose_name='الحد الأقصى للسن')
#     order     = models.PositiveIntegerField(default=0, verbose_name='الترتيب')
#     is_active = models.BooleanField(default=True, verbose_name='نشطة')

#     def clean(self):
#         if self.min_age >= self.max_age:
#             raise ValidationError('الحد الأدنى يجب أن يكون أقل من الحد الأقصى')

#     def __str__(self):
#         return f"{self.name} ({self.min_age} - {self.max_age} سنة)"

#     class Meta:
#         verbose_name        = 'فئة عمرية'
#         verbose_name_plural = 'الفئات العمرية'
#         ordering            = ['order', 'min_age']


# class Student(models.Model):
#     STATUS_PENDING  = 'pending'
#     STATUS_ACTIVE   = 'active'
#     STATUS_INACTIVE = 'inactive'

#     STATUS_CHOICES = [
#         (STATUS_PENDING,  'في انتظار التسكين'),
#         (STATUS_ACTIVE,   'نشط'),
#         (STATUS_INACTIVE, 'غير نشط'),
#     ]

#     # بيانات الطالب الأساسية
#     first_name      = models.CharField(max_length=50, verbose_name='الاسم الأول')
#     last_name       = models.CharField(max_length=50, verbose_name='اسم العائلة')
#     date_of_birth   = models.DateField(verbose_name='تاريخ الميلاد')
#     age_group       = models.ForeignKey(
#                         'students.AgeGroup',
#                         on_delete=models.SET_NULL,
#                         null=True,
#                         blank=True,
#                         related_name='students',
#                         verbose_name='الفئة العمرية'
#                     )

#     # age_group       = models.ForeignKey(
#     #                       AgeGroup,
#     #                       on_delete=models.SET_NULL,
#     #                       null=True,
#     #                       blank=True,
#     #                       related_name='students',
#     #                       verbose_name='الفئة العمرية'
#     #                   )
#     profile_picture = models.ImageField(
#                           upload_to='students/',
#                           blank=True,
#                           null=True,
#                           verbose_name='صورة الطالب'
#                       )

#     # السور المحفوظة
#     memorized_surahs = models.ManyToManyField(
#                            Surah,
#                            blank=True,
#                            verbose_name='السور المحفوظة',
#                            related_name='memorized_by'
#                        )

#     # ولي الأمر والقاعة
#     parent = models.ForeignKey(
#                  User,
#                  on_delete=models.CASCADE,
#                  related_name='children',
#                  limit_choices_to={'role': 'parent'},
#                  verbose_name='ولي الأمر'
#              )
#     hall   = models.ForeignKey(
#                  'halls.Hall',
#                  on_delete=models.SET_NULL,
#                  null=True,
#                  blank=True,
#                  related_name='students',
#                  verbose_name='القاعة'
#              )

#     # خدمة الباص
#     uses_bus  = models.BooleanField(default=False, verbose_name='يشترك في الباص')
#     bus_notes = models.CharField(max_length=200, blank=True, verbose_name='ملاحظات الباص')

#     # الحالة والتسجيل
#     status            = models.CharField(
#                             max_length=20,
#                             choices=STATUS_CHOICES,
#                             default=STATUS_PENDING,
#                             verbose_name='حالة الطالب'
#                         )
#     registration_date = models.DateField(auto_now_add=True, verbose_name='تاريخ التسجيل')
#     notes             = models.TextField(blank=True, verbose_name='ملاحظات عامة')

#     # ====== Methods ======

#     def get_full_name(self):
#         return f"{self.first_name} {self.last_name}"

#     def calculate_age(self):
#         from datetime import date
#         today = date.today()
#         born  = self.date_of_birth
#         return today.year - born.year - (
#             (today.month, today.day) < (born.month, born.day)
#         )

#     def get_matching_age_group(self):
#         """إيجاد الفئة العمرية المناسبة تلقائياً"""
#         age = self.calculate_age()
#         return AgeGroup.objects.filter(
#             min_age__lte=age,
#             max_age__gte=age,
#             is_active=True
#         ).order_by('order').first()

#     def get_memorization_level(self):
#         return self.memorized_surahs.count()

#     def save(self, *args, **kwargs):
#         """تحديد الفئة العمرية تلقائياً عند الحفظ"""
#         matched = self.get_matching_age_group()
#         if matched:
#             self.age_group = matched
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return f"{self.get_full_name()} ({self.calculate_age()} سنة)"

#     class Meta:
#         verbose_name        = 'طالب'
#         verbose_name_plural = 'الطلاب'
#         ordering            = ['first_name', 'last_name']
