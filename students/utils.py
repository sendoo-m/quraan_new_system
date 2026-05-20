from .models import Student, AgeGroup
from halls.models import Hall


def auto_assign_hall(student):
    age           = student.calculate_age()
    completed_juz = student.get_completed_juz_count()

    # الجزء المستحق = 30 - عدد الأجزاء المكتملة
    # مثال: أكمل 0 → جزء 30 | أكمل 1 → جزء 29 | أكمل 3 → جزء 27
    target_juz = 30 - completed_juz
    if target_juz < 1:
        target_juz = 1  # احتياط إذا كان حافظاً للقرآن كاملاً

    # الفئات العمرية المناسبة لعمر الطالب
    matching_age_groups = AgeGroup.objects.filter(
        min_age__lte=age,
        max_age__gte=age,
        is_active=True
    )

    if not matching_age_groups.exists():
        student.status    = Student.STATUS_REJECTED
        student.age_group = None
        student.save(update_fields=['status', 'age_group'])
        return None, f'لا توجد فئة عمرية تناسب عمر الطالب ({age} سنة)'

    # البحث عن قاعة تطابق:
    # 1. الفئة العمرية
    # 2. current_juz == target_juz (الجزء المستحق للطالب)
    # 3. عدد الأجزاء المكتملة >= required_completed_juz_count
    available_halls = Hall.objects.filter(
        age_group__in=matching_age_groups,
        is_active=True,
        current_juz=target_juz,
        required_completed_juz_count__lte=completed_juz
    ).order_by('-required_completed_juz_count', 'name')

    for hall in available_halls:
        accepted, reason = hall.accepts_student(student)
        if accepted:
            student.age_group = hall.age_group
            student.hall      = hall
            student.status    = Student.STATUS_ACTIVE
            student.save()
            return hall, f'تم تسكين {student.get_full_name()} في {hall.name}'

    # لم يوجد تطابق مع current_juz — ابحث عن أقرب قاعة بجزء مناسب
    fallback_halls = Hall.objects.filter(
        age_group__in=matching_age_groups,
        is_active=True,
        current_juz__gte=target_juz,  # قاعات بجزء أعلى أو مساوٍ (أقل حفظاً مطلوباً)
        required_completed_juz_count__lte=completed_juz
    ).order_by('current_juz', '-required_completed_juz_count', 'name')

    for hall in fallback_halls:
        accepted, reason = hall.accepts_student(student)
        if accepted:
            student.age_group = hall.age_group
            student.hall      = hall
            student.status    = Student.STATUS_ACTIVE
            student.save()
            return hall, f'تم تسكين {student.get_full_name()} في {hall.name}'

    # لا توجد قاعة مناسبة
    best_age_group = matching_age_groups.order_by('order', 'min_age').first()
    student.age_group = best_age_group
    student.status    = Student.STATUS_REJECTED
    student.save()
    return None, 'لا توجد قاعة مناسبة لمستوى الحفظ والعمر أو تم اكتمال العدد'


def transfer_student(student, new_hall):
    accepted, reason = new_hall.accepts_student(student)
    if not accepted:
        return False, reason

    student.hall      = new_hall
    student.age_group = new_hall.age_group
    student.status    = Student.STATUS_ACTIVE
    student.save()
    return True, f'تم نقل {student.get_full_name()} إلى {new_hall.name}'

# from .models import Student, AgeGroup
# from halls.models import Hall


# def auto_assign_hall(student):
#     age = student.calculate_age()
#     student_juz = student.get_completed_juz_count()

#     # جلب كل الفئات التي يقع عمر الطالب ضمنها
#     matching_age_groups = AgeGroup.objects.filter(
#         min_age__lte=age,
#         max_age__gte=age,
#         is_active=True
#     )

#     if not matching_age_groups.exists():
#         student.status = Student.STATUS_REJECTED
#         student.age_group = None
#         student.save(update_fields=['status', 'age_group'])
#         return None, f'لا توجد فئة عمرية تناسب عمر الطالب ({age} سنة)'

#     # جلب كل القاعات من كل الفئات المطابقة للعمر
#     # مع فلترة الأجزاء مباشرة وترتيب تنازلي بالمستوى
#     available_halls = Hall.objects.filter(
#         age_group__in=matching_age_groups,
#         is_active=True,
#         required_completed_juz_count__lte=student_juz
#     ).order_by('-required_completed_juz_count', 'name')

#     for hall in available_halls:
#         accepted, reason = hall.accepts_student(student)
#         if accepted:
#             student.age_group = hall.age_group  # ← الفئة من القاعة المختارة
#             student.hall = hall
#             student.status = Student.STATUS_ACTIVE
#             student.save()
#             return hall, f'تم تسكين {student.get_full_name()} في {hall.name}'

#     # لم تُقبل في أي قاعة — نحفظ الفئة الأنسب للعمر فقط
#     best_age_group = matching_age_groups.order_by('order', 'min_age').first()
#     student.age_group = best_age_group
#     student.status = Student.STATUS_REJECTED
#     student.save()
#     return None, 'لا توجد قاعة مناسبة لمستوى الحفظ والعمر أو تم اكتمال العدد'


# def transfer_student(student, new_hall):
#     accepted, reason = new_hall.accepts_student(student)
#     if not accepted:
#         return False, reason

#     student.hall = new_hall
#     student.age_group = new_hall.age_group  # ← تحديث الفئة عند النقل أيضاً
#     student.status = Student.STATUS_ACTIVE
#     student.save()
#     return True, f'تم نقل {student.get_full_name()} إلى {new_hall.name}'
