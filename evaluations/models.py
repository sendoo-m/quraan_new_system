from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User
from students.models import Student
from halls.models import Hall


class DailyFollowUp(models.Model):
    """
    المتابعة اليومية — يكتبها مشرف القاعة
    تظهر لأولياء الأمور
    """
    hall        = models.ForeignKey(
                      Hall,
                      on_delete=models.CASCADE,
                      related_name='daily_followups',
                      verbose_name='القاعة'
                  )
    date        = models.DateField(default=timezone.now, verbose_name='التاريخ')
    homework    = models.TextField(verbose_name='الواجب المطلوب')
    memorization_task = models.TextField(
                            blank=True,
                            verbose_name='المطلوب حفظه'
                        )
    extra_notes = models.TextField(blank=True, verbose_name='ملاحظات إضافية')
    created_by  = models.ForeignKey(
                      User,
                      on_delete=models.SET_NULL,
                      null=True,
                      related_name='followups_created',
                      limit_choices_to={'role__in': ['hall_supervisor', 'general_supervisor', 'general_manager']},
                      verbose_name='كتبه'
                  )
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"متابعة {self.hall.name} | {self.date}"

    class Meta:
        verbose_name        = 'متابعة يومية'
        verbose_name_plural = 'المتابعات اليومية'
        ordering            = ['-date']
        unique_together     = ['hall', 'date']


class StudentEvaluation(models.Model):
    """
    تقييم الطالب — يكتبه المعلم
    يظهر لولي الأمر
    """
    RATING_EXCELLENT = 'excellent'
    RATING_GOOD      = 'good'
    RATING_AVERAGE   = 'average'
    RATING_WEAK      = 'weak'

    RATING_CHOICES = [
        (RATING_EXCELLENT, '⭐ ممتاز'),
        (RATING_GOOD,      '✅ جيد'),
        (RATING_AVERAGE,   '➖ متوسط'),
        (RATING_WEAK,      '⚠️ يحتاج متابعة'),
    ]

    student             = models.ForeignKey(
                              Student,
                              on_delete=models.CASCADE,
                              related_name='evaluations',
                              verbose_name='الطالب'
                          )
    date                = models.DateField(default=timezone.now, verbose_name='التاريخ')

    # تقييم الحفظ
    memorization_rating = models.CharField(
                              max_length=15,
                              choices=RATING_CHOICES,
                              verbose_name='تقييم الحفظ'
                          )
    memorization_notes  = models.TextField(blank=True, verbose_name='ملاحظات الحفظ')

    # السلوك والالتزام
    behavior_rating     = models.CharField(
                              max_length=15,
                              choices=RATING_CHOICES,
                              verbose_name='تقييم السلوك'
                          )
    commitment_rating   = models.CharField(
                              max_length=15,
                              choices=RATING_CHOICES,
                              verbose_name='تقييم الالتزام'
                          )
    behavior_notes      = models.TextField(blank=True, verbose_name='ملاحظات السلوك')

    # تمييز الطالب
    is_distinguished    = models.BooleanField(default=False, verbose_name='متميز')
    needs_attention     = models.BooleanField(default=False, verbose_name='يحتاج متابعة')
    general_notes       = models.TextField(blank=True, verbose_name='ملاحظات عامة لولي الأمر')

    teacher             = models.ForeignKey(
                              User,
                              on_delete=models.SET_NULL,
                              null=True,
                              related_name='evaluations_given',
                              limit_choices_to={'role__in': ['teacher', 'general_supervisor', 'general_manager']},
                              verbose_name='المعلم'
                          )
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"تقييم {self.student.get_full_name()} | {self.date}"

    class Meta:
        verbose_name        = 'تقييم طالب'
        verbose_name_plural = 'تقييمات الطلاب'
        ordering            = ['-date']
        unique_together     = ['student', 'date']
