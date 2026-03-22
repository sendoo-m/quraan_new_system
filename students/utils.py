from .models import Student, AgeGroup
from halls.models import Hall


def auto_assign_hall(student):
    age_group = student.get_matching_age_group()

    if not age_group:
        age = student.calculate_age()
        return None, f'لا توجد فئة عمرية تناسب عمر الطالب ({age} سنة)'

    # البحث عن قاعة بنفس الفئة العمرية وفيها مكان
    available_halls = Hall.objects.filter(
        age_group=age_group,
        is_active=True
    )

    for hall in available_halls:
        if hall.has_available_seats():
            student.hall   = hall
            student.status = Student.STATUS_ACTIVE
            student.save()
            return hall, f'تم تسكين الطالب في {hall.name}'

    return None, f'لا توجد قاعة متاحة للفئة: {age_group.name}'


def transfer_student(student, new_hall):
    if not new_hall.has_available_seats():
        return False, 'القاعة الجديدة ممتلئة'

    if new_hall.age_group != student.age_group:
        return False, f'الفئة العمرية للقاعة ({new_hall.age_group}) لا تناسب الطالب ({student.age_group})'

    student.hall = new_hall
    student.save()
    return True, f'تم نقل {student.get_full_name()} إلى {new_hall.name}'

# from .models import Student
# from halls.models import Hall


# def auto_assign_hall(student):
#     """
#     تسكين الطالب تلقائياً بناءً على:
#     1. الفئة العمرية
#     2. توفر مقاعد
#     """
#     age_group = student.get_age_group()

#     if not age_group:
#         return None, 'عمر الطالب خارج النطاق المقبول (3-15 سنة)'

#     # البحث عن قاعة مناسبة بنفس الفئة العمرية وفيها مكان
#     available_halls = Hall.objects.filter(
#         age_group=age_group,
#         is_active=True
#     )

#     for hall in available_halls:
#         if hall.has_available_seats():
#             student.hall    = hall
#             student.status  = Student.STATUS_ACTIVE
#             student.save()
#             return hall, 'تم التسكين بنجاح'

#     # لو مفيش قاعة متاحة
#     return None, 'لا توجد قاعة متاحة لهذه الفئة العمرية حالياً'


# def transfer_student(student, new_hall):
#     """نقل طالب من قاعة لقاعة — صلاحية المشرف العام"""
#     if not new_hall.has_available_seats():
#         return False, 'القاعة الجديدة ممتلئة'

#     if new_hall.age_group != student.age_group:
#         return False, 'الفئة العمرية للقاعة لا تناسب الطالب'

#     student.hall = new_hall
#     student.save()
#     return True, f'تم نقل {student.get_full_name()} إلى {new_hall.name}'
