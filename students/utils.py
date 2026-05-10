from .models import Student, AgeGroup
from halls.models import Hall


def auto_assign_hall(student):
    age = student.calculate_age()
    student_juz = student.get_completed_juz_count()

    # جلب كل الفئات التي يقع عمر الطالب ضمنها
    matching_age_groups = AgeGroup.objects.filter(
        min_age__lte=age,
        max_age__gte=age,
        is_active=True
    )

    if not matching_age_groups.exists():
        student.status = Student.STATUS_REJECTED
        student.age_group = None
        student.save(update_fields=['status', 'age_group'])
        return None, f'لا توجد فئة عمرية تناسب عمر الطالب ({age} سنة)'

    # جلب كل القاعات من كل الفئات المطابقة للعمر
    # مع فلترة الأجزاء مباشرة وترتيب تنازلي بالمستوى
    available_halls = Hall.objects.filter(
        age_group__in=matching_age_groups,
        is_active=True,
        required_completed_juz_count__lte=student_juz
    ).order_by('-required_completed_juz_count', 'name')

    for hall in available_halls:
        accepted, reason = hall.accepts_student(student)
        if accepted:
            student.age_group = hall.age_group  # ← الفئة من القاعة المختارة
            student.hall = hall
            student.status = Student.STATUS_ACTIVE
            student.save()
            return hall, f'تم تسكين {student.get_full_name()} في {hall.name}'

    # لم تُقبل في أي قاعة — نحفظ الفئة الأنسب للعمر فقط
    best_age_group = matching_age_groups.order_by('order', 'min_age').first()
    student.age_group = best_age_group
    student.status = Student.STATUS_REJECTED
    student.save()
    return None, 'لا توجد قاعة مناسبة لمستوى الحفظ والعمر أو تم اكتمال العدد'


def transfer_student(student, new_hall):
    accepted, reason = new_hall.accepts_student(student)
    if not accepted:
        return False, reason

    student.hall = new_hall
    student.age_group = new_hall.age_group  # ← تحديث الفئة عند النقل أيضاً
    student.status = Student.STATUS_ACTIVE
    student.save()
    return True, f'تم نقل {student.get_full_name()} إلى {new_hall.name}'

# from .models import Student
# from halls.models import Hall


# def auto_assign_hall(student):
#     age_group = student.get_matching_age_group()
#     if not age_group:
#         age = student.calculate_age()
#         student.status = Student.STATUS_REJECTED
#         student.save(update_fields=['status', 'age_group'])
#         return None, f'لا توجد فئة عمرية تناسب عمر الطالب ({age} سنة)'

#     available_halls = Hall.objects.filter(
#         age_group=age_group,
#         is_active=True
#     ).order_by('current_juz', 'name')

#     for hall in available_halls:
#         accepted, reason = hall.accepts_student(student)
#         if accepted:
#             student.age_group = age_group
#             student.hall = hall
#             student.status = Student.STATUS_ACTIVE
#             student.save()
#             return hall, f'تم تسكين الطالب في {hall.name}'

#     student.age_group = age_group
#     student.status = Student.STATUS_REJECTED
#     student.save()
#     return None, 'تم اكتمال العدد بالقاعة أو لا توجد قاعة مناسبة لمستوى الحفظ والعمر'


# def transfer_student(student, new_hall):
#     accepted, reason = new_hall.accepts_student(student)
#     if not accepted:
#         return False, reason

#     student.hall = new_hall
#     student.status = Student.STATUS_ACTIVE
#     student.save()
#     return True, f'تم نقل {student.get_full_name()} إلى {new_hall.name}'

