from .models import Student
from halls.models import Hall


def auto_assign_hall(student):
    age_group = student.get_matching_age_group()
    if not age_group:
        age = student.calculate_age()
        student.status = Student.STATUS_REJECTED
        student.save(update_fields=['status', 'age_group'])
        return None, f'لا توجد فئة عمرية تناسب عمر الطالب ({age} سنة)'

    available_halls = Hall.objects.filter(
        age_group=age_group,
        is_active=True
    ).order_by('current_juz', 'name')

    for hall in available_halls:
        accepted, reason = hall.accepts_student(student)
        if accepted:
            student.age_group = age_group
            student.hall = hall
            student.status = Student.STATUS_ACTIVE
            student.save()
            return hall, f'تم تسكين الطالب في {hall.name}'

    student.age_group = age_group
    student.status = Student.STATUS_REJECTED
    student.save()
    return None, 'تم اكتمال العدد بالقاعة أو لا توجد قاعة مناسبة لمستوى الحفظ والعمر'


def transfer_student(student, new_hall):
    accepted, reason = new_hall.accepts_student(student)
    if not accepted:
        return False, reason

    student.hall = new_hall
    student.status = Student.STATUS_ACTIVE
    student.save()
    return True, f'تم نقل {student.get_full_name()} إلى {new_hall.name}'


# from .models import Student, AgeGroup
# from halls.models import Hall


# def auto_assign_hall(student):
#     age_group = student.get_matching_age_group()

#     if not age_group:
#         age = student.calculate_age()
#         return None, f'لا توجد فئة عمرية تناسب عمر الطالب ({age} سنة)'

#     # البحث عن قاعة بنفس الفئة العمرية وفيها مكان
#     available_halls = Hall.objects.filter(
#         age_group=age_group,
#         is_active=True
#     )

#     for hall in available_halls:
#         if hall.has_available_seats():
#             student.hall   = hall
#             student.status = Student.STATUS_ACTIVE
#             student.save()
#             return hall, f'تم تسكين الطالب في {hall.name}'

#     return None, f'لا توجد قاعة متاحة للفئة: {age_group.name}'


# def transfer_student(student, new_hall):
#     if not new_hall.has_available_seats():
#         return False, 'القاعة الجديدة ممتلئة'

#     if new_hall.age_group != student.age_group:
#         return False, f'الفئة العمرية للقاعة ({new_hall.age_group}) لا تناسب الطالب ({student.age_group})'

#     student.hall = new_hall
#     student.save()
#     return True, f'تم نقل {student.get_full_name()} إلى {new_hall.name}'
