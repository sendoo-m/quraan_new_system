from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget
from django.db.models import Count
from .models import Student, AgeGroup
from accounts.models import User
from halls.models import Hall
from quran.models import Surah


def clean_cell(value, default=''):
    if value is None:
        return default
    return str(value).strip()


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
        widget=ManyToManyWidget(Surah, field='name_arabic', separator='|')
    )

    class Meta:
        model = Student
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
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        for key in [
            'id', 'first_name', 'last_name', 'date_of_birth',
            'الفئة العمرية', 'ولي الأمر', 'القاعة', 'status',
            'uses_bus', 'bus_notes', 'emergency_phone',
            'السور المحفوظة', 'registration_date', 'notes'
        ]:
            row[key] = clean_cell(row.get(key))

        if not row['notes']:
            row['notes'] = ''

        if not row['bus_notes']:
            row['bus_notes'] = ''

        if not row['emergency_phone']:
            row['emergency_phone'] = ''

        if not row['القاعة']:
            row['القاعة'] = None

        if not row['الفئة العمرية']:
            row['الفئة العمرية'] = None

    def get_instance(self, instance_loader, row):
        student_id = clean_cell(row.get('id'))
        if student_id:
            return self._meta.model.objects.filter(id=student_id).first()

        parent_username = clean_cell(row.get('ولي الأمر'))
        first_name = clean_cell(row.get('first_name'))
        last_name = clean_cell(row.get('last_name'))

        if parent_username and first_name and last_name:
            return self._meta.model.objects.filter(
                parent__username=parent_username,
                first_name=first_name,
                last_name=last_name,
            ).first()

        return None