from django.contrib import admin
from .models import Surah


@admin.register(Surah)
class SurahAdmin(admin.ModelAdmin):
    list_display = ('number', 'name_arabic', 'name_english', 'juz', 'total_verses')
    list_filter = ('juz',)
    search_fields = ('name_arabic', 'name_english', 'number')
    ordering = ('number',)
    fieldsets = (
        (None, {
            'fields': ('number', 'name_arabic', 'name_english', 'juz', 'total_verses')
        }),
    )
    class Meta:
        verbose_name = 'سورة'
        verbose_name_plural = 'سور القرآن الكريم'