from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import Hall, Subject, ScheduleTemplate
from accounts.models import User
from students.models import AgeGroup


class HallResource(resources.ModelResource):
    age_group = fields.Field(
        column_name='الفئة العمرية',
        attribute='age_group',
        widget=ForeignKeyWidget(AgeGroup, field='name')
    )
    teacher = fields.Field(
        column_name='المعلم',
        attribute='teacher',
        widget=ForeignKeyWidget(User, field='username')
    )
    supervisor = fields.Field(
        column_name='مشرف القاعة',
        attribute='supervisor',
        widget=ForeignKeyWidget(User, field='username')
    )
    general_supervisor = fields.Field(
        column_name='المشرف العام',
        attribute='general_supervisor',
        widget=ForeignKeyWidget(User, field='username')
    )

    class Meta:
        model  = Hall
        fields = (
            'id',
            'name',
            'location',
            'age_group',
            'max_students',
            'current_juz',
            'required_completed_juz_count',
            'teacher',
            'supervisor',
            'general_supervisor',
            'is_active',
        )
        export_order = fields
        import_id_fields = ['id']


class SubjectResource(resources.ModelResource):
    class Meta:
        model  = Subject
        fields = ('id', 'name', 'description', 'is_active')


class ScheduleTemplateResource(resources.ModelResource):
    class Meta:
        model  = ScheduleTemplate
        fields = ('id', 'name', 'description', 'is_active')