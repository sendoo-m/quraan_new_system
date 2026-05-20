from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget
from .models import Student, AgeGroup
from accounts.models import User
from halls.models import Hall
from quran.models import Surah


class StudentResource(resources.ModelResource):
    parent = fields.Field(
        column_name='ولي الأمر',
        attribute='parent',
        widget=ForeignKeyWidget(User, field='username')
    )
    hall = fields.Field(
        column_name='القاعة',
        attribute='hall',
        widget=ForeignKeyWidget(Hall, field='name')
    )
    age_group = fields.Field(
        column_name='الفئة العمرية',
        attribute='age_group',
        widget=ForeignKeyWidget(AgeGroup, field='name')
    )
    memorized_surahs = fields.Field(
        column_name='السور المحفوظة',
        attribute='memorized_surahs',
        widget=ManyToManyWidget(Surah, field='name', separator='|')
    )

    class Meta:
        model  = Student
        fields = (
            'id',
            'first_name',
            'last_name',
            'date_of_birth',
            'age_group',
            'parent',
            'hall',
            'status',
            'uses_bus',
            'bus_notes',
            'emergency_phone',
            'memorized_surahs',
            'registration_date',
            'notes',
        )
        export_order = fields
        import_id_fields = ['id']

    def get_export_queryset(self, queryset, *args, **kwargs):
        return queryset.select_related(
            'parent', 'hall', 'age_group'
        ).prefetch_related('memorized_surahs')