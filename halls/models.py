from django.db import models
from accounts.models import User


class Hall(models.Model):
    name = models.CharField(max_length=100, verbose_name='اسم القاعة')
    location = models.CharField(max_length=200, verbose_name='موقع القاعة')
    age_group = models.ForeignKey(
        'students.AgeGroup',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='halls',
        verbose_name='الفئة العمرية'
    )
    max_students = models.PositiveIntegerField(default=30, verbose_name='أقصى عدد للطلاب')

    general_supervisor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_halls',
        limit_choices_to={'role': 'general_supervisor'},
        verbose_name='المشرف العام المسؤول'
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teaching_halls',
        limit_choices_to={'role': 'teacher'},
        verbose_name='المعلم'
    )
    supervisor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supervising_halls',
        limit_choices_to={'role': 'hall_supervisor'},
        verbose_name='مشرف القاعة'
    )

    current_juz = models.PositiveIntegerField(
        default=30,
        verbose_name='الجزء الحالي الذي تبدأ منه القاعة'
    )
    required_completed_juz_count = models.PositiveIntegerField(
        default=0,
        verbose_name='عدد الأجزاء المطلوبة قبل دخول القاعة'
    )

    is_active = models.BooleanField(default=True, verbose_name='نشطة')
    created_at = models.DateTimeField(auto_now_add=True)

    # ══════════════════════════════════════════
    def get_current_students_count(self):
        return self.students.filter(status='active').count()

    def has_available_seats(self):
        return self.get_current_students_count() < self.max_students

    def get_available_seats(self):
        return self.max_students - self.get_current_students_count()

    def accepts_student(self, student):
        """
        تفحص إن كانت القاعة تقبل الطالب بناءً على:
        1. القاعة نشطة
        2. يوجد مقاعد متاحة
        3. عمر الطالب ضمن نطاق الفئة العمرية للقاعة
        4. عدد الأجزاء المحفوظة يساوي أو يزيد على الحد المطلوب
        """
        if not self.is_active:
            return False, 'القاعة غير نشطة'

        if not self.has_available_seats():
            return False, f'تم اكتمال العدد ({self.max_students} طالب)'

        # ← التغيير: فحص العمر مباشرة بدل مقارنة age_group_id
        if self.age_group:
            age = student.calculate_age()
            if not (self.age_group.min_age <= age <= self.age_group.max_age):
                return False, (
                    f'عمر الطالب ({age} سنة) خارج نطاق القاعة '
                    f'({self.age_group.min_age}–{self.age_group.max_age} سنة)'
                )

        student_juz = student.get_completed_juz_count()
        if student_juz < self.required_completed_juz_count:
            return False, (
                f'مستوى الحفظ غير كافٍ — '
                f'الطالب أتمّ {student_juz} جزء '
                f'والمطلوب {self.required_completed_juz_count} جزء'
            )

        return True, 'الطالب مناسب للقاعة'

    # ══════════════════════════════════════════
    def __str__(self):
        ag = self.age_group.name if self.age_group else 'بدون فئة'
        return f"{self.name} — {ag}"

    class Meta:
        verbose_name = 'قاعة'
        verbose_name_plural = 'القاعات'
        ordering = ['name']


class Subject(models.Model):
    name = models.CharField(max_length=100, verbose_name='اسم المادة')
    description = models.TextField(blank=True, verbose_name='وصف المادة')
    is_active = models.BooleanField(default=True, verbose_name='نشطة')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'مادة'
        verbose_name_plural = 'المواد الدراسية'


class HallSchedule(models.Model):
    DAYS = [
        ('sunday',   'الأحد'),
        ('tuesday',  'الثلاثاء'),
        ('thursday', 'الخميس'),
    ]

    hall = models.ForeignKey(
        Hall,
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name='القاعة'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        verbose_name='المادة'
    )
    day        = models.CharField(max_length=15, choices=DAYS, verbose_name='اليوم')
    start_time = models.TimeField(verbose_name='وقت البداية')
    end_time   = models.TimeField(verbose_name='وقت النهاية')

    def __str__(self):
        return f"{self.hall.name} | {self.subject.name} | {self.get_day_display()}"

    class Meta:
        verbose_name        = 'جدول قاعة'
        verbose_name_plural = 'جداول القاعات'
        ordering            = ['day', 'start_time']
        unique_together     = ['hall', 'day', 'start_time']