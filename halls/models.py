from django.db import models
from accounts.models import User


class Hall(models.Model):
    name         = models.CharField(max_length=100, verbose_name='اسم القاعة')
    location     = models.CharField(max_length=200, verbose_name='موقع القاعة')
    age_group    = models.ForeignKey(
                       'students.AgeGroup',          # ← ForeignKey بدل choices
                       on_delete=models.SET_NULL,
                       null=True,
                       blank=True,
                       related_name='halls',
                       verbose_name='الفئة العمرية'
                   )
    max_students = models.PositiveIntegerField(
                       default=30,
                       verbose_name='أقصى عدد للطلاب'
                   )
    teacher      = models.ForeignKey(
                       User,
                       on_delete=models.SET_NULL,
                       null=True,
                       blank=True,
                       related_name='teaching_halls',
                       limit_choices_to={'role': 'teacher'},
                       verbose_name='المعلم'
                   )
    supervisor   = models.ForeignKey(
                       User,
                       on_delete=models.SET_NULL,
                       null=True,
                       blank=True,
                       related_name='supervising_halls',
                       limit_choices_to={'role': 'hall_supervisor'},
                       verbose_name='مشرف القاعة'
                   )
    is_active    = models.BooleanField(default=True, verbose_name='نشطة')
    created_at   = models.DateTimeField(auto_now_add=True)

    # ====== Methods ======

    def get_current_students_count(self):
        return self.students.filter(status='active').count()

    def has_available_seats(self):
        return self.get_current_students_count() < self.max_students

    def get_available_seats(self):
        return self.max_students - self.get_current_students_count()

    def __str__(self):
        ag = self.age_group.name if self.age_group else 'بدون فئة'
        return f"{self.name} — {ag}"

    class Meta:
        verbose_name        = 'قاعة'
        verbose_name_plural = 'القاعات'
        ordering            = ['name']


class Subject(models.Model):
    name        = models.CharField(max_length=100, verbose_name='اسم المادة')
    description = models.TextField(blank=True, verbose_name='وصف المادة')
    is_active   = models.BooleanField(default=True, verbose_name='نشطة')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name        = 'مادة'
        verbose_name_plural = 'المواد الدراسية'


class HallSchedule(models.Model):
    DAYS = [
        ('saturday',  'السبت'),
        ('sunday',    'الأحد'),
        ('monday',    'الاثنين'),
        ('tuesday',   'الثلاثاء'),
        ('wednesday', 'الأربعاء'),
        ('thursday',  'الخميس'),
        ('friday',    'الجمعة'),
    ]

    hall       = models.ForeignKey(
                     Hall,
                     on_delete=models.CASCADE,
                     related_name='schedules',
                     verbose_name='القاعة'
                 )
    subject    = models.ForeignKey(
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

# from django.db import models
# from accounts.models import User


# class Hall(models.Model):
#     AGE_GROUP_3_4   = 'group_3_4'
#     AGE_GROUP_5_7   = 'group_5_7'
#     AGE_GROUP_8_10  = 'group_8_10'
#     AGE_GROUP_11_15 = 'group_11_15'

#     AGE_GROUPS = [
#         (AGE_GROUP_3_4,   'من 3 إلى 4 سنوات'),
#         (AGE_GROUP_5_7,   'من 5 إلى 7 سنوات'),
#         (AGE_GROUP_8_10,  'من 8 إلى 10 سنوات'),
#         (AGE_GROUP_11_15, 'من 11 إلى 15 سنة'),
#     ]

#     name          = models.CharField(max_length=100, verbose_name='اسم القاعة')
#     location      = models.CharField(max_length=200, verbose_name='موقع القاعة')
#     age_group     = models.CharField(
#                         max_length=20,
#                         choices=AGE_GROUPS,
#                         verbose_name='الفئة العمرية'
#                     )
#     max_students  = models.PositiveIntegerField(
#                         default=30,
#                         verbose_name='أقصى عدد للطلاب'
#                     )
#     teacher       = models.ForeignKey(
#                         User,
#                         on_delete=models.SET_NULL,
#                         null=True,
#                         blank=True,
#                         related_name='teaching_halls',
#                         limit_choices_to={'role': 'teacher'},
#                         verbose_name='المعلم'
#                     )
#     supervisor    = models.ForeignKey(
#                         User,
#                         on_delete=models.SET_NULL,
#                         null=True,
#                         blank=True,
#                         related_name='supervising_halls',
#                         limit_choices_to={'role': 'hall_supervisor'},
#                         verbose_name='مشرف القاعة'
#                     )
#     is_active     = models.BooleanField(default=True, verbose_name='نشطة')
#     created_at    = models.DateTimeField(auto_now_add=True)

#     # ====== Methods ======

#     def get_current_students_count(self):
#         return self.students.filter(status='active').count()

#     def has_available_seats(self):
#         return self.get_current_students_count() < self.max_students

#     def get_available_seats(self):
#         return self.max_students - self.get_current_students_count()

#     def __str__(self):
#         return f"{self.name} — {self.get_age_group_display()}"

#     class Meta:
#         verbose_name        = 'قاعة'
#         verbose_name_plural = 'القاعات'
#         ordering            = ['name']


# class Subject(models.Model):
#     name       = models.CharField(max_length=100, verbose_name='اسم المادة')
#     description = models.TextField(blank=True, verbose_name='وصف المادة')
#     is_active  = models.BooleanField(default=True, verbose_name='نشطة')

#     def __str__(self):
#         return self.name

#     class Meta:
#         verbose_name        = 'مادة'
#         verbose_name_plural = 'المواد الدراسية'


# class HallSchedule(models.Model):
#     DAYS = [
#         ('saturday',  'السبت'),
#         ('sunday',    'الأحد'),
#         ('monday',    'الاثنين'),
#         ('tuesday',   'الثلاثاء'),
#         ('wednesday', 'الأربعاء'),
#         ('thursday',  'الخميس'),
#         ('friday',    'الجمعة'),
#     ]

#     hall       = models.ForeignKey(
#                      Hall,
#                      on_delete=models.CASCADE,
#                      related_name='schedules',
#                      verbose_name='القاعة'
#                  )
#     subject    = models.ForeignKey(
#                      Subject,
#                      on_delete=models.CASCADE,
#                      verbose_name='المادة'
#                  )
#     day        = models.CharField(max_length=15, choices=DAYS, verbose_name='اليوم')
#     start_time = models.TimeField(verbose_name='وقت البداية')
#     end_time   = models.TimeField(verbose_name='وقت النهاية')

#     def __str__(self):
#         return f"{self.hall.name} | {self.subject.name} | {self.get_day_display()}"

#     class Meta:
#         verbose_name        = 'جدول قاعة'
#         verbose_name_plural = 'جداول القاعات'
#         ordering            = ['day', 'start_time']
#         unique_together     = ['hall', 'day', 'start_time']
