from django.db import models


class Surah(models.Model):
    number = models.PositiveIntegerField(unique=True, verbose_name='رقم السورة')
    name_arabic = models.CharField(max_length=50, verbose_name='اسم السورة')
    name_english = models.CharField(max_length=50, verbose_name='الاسم بالإنجليزي')
    juz = models.PositiveIntegerField(verbose_name='الجزء')
    total_verses = models.PositiveIntegerField(verbose_name='عدد الآيات')

    def __str__(self):
        return f"{self.number}. {self.name_arabic}"

    class Meta:
        ordering = ['number']
        verbose_name = 'سورة'
        verbose_name_plural = 'سور القرآن الكريم'
