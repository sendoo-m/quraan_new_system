from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from halls.models import Hall


class BasePermissionMixin(UserPassesTestMixin):
    def handle_no_permission(self):
        raise PermissionDenied("ليس لديك صلاحية للوصول إلى هذه الصفحة")


class GeneralManagerRequiredMixin(BasePermissionMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_general_manager


class GeneralSupervisorRequiredMixin(BasePermissionMixin):
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (
            user.is_general_manager or
            user.is_general_supervisor
        )


class HallSupervisorRequiredMixin(BasePermissionMixin):
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (
            user.is_general_manager or
            user.is_general_supervisor or
            user.is_hall_supervisor
        )


class TeacherRequiredMixin(BasePermissionMixin):
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (
            user.is_general_manager or
            user.is_general_supervisor or
            user.is_teacher
        )


class StaffRequiredMixin(BasePermissionMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff_member


class ParentRequiredMixin(BasePermissionMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_parent


def user_can_access_hall(user, hall):
    if not user.is_authenticated:
        return False
    if user.is_general_manager:
        return True
    if user.is_general_supervisor:
        return user.hall_assignments.filter(hall=hall).exists()
    if user.is_hall_supervisor:
        return hall.supervisor_id == user.id
    if user.is_teacher:
        return hall.teacher_id == user.id
    return False


def user_can_access_student(user, student):
    if not user.is_authenticated:
        return False
    if user.is_general_manager:
        return True
    if user.is_general_supervisor:
        return student.hall and user.hall_assignments.filter(hall=student.hall).exists()
    if user.is_hall_supervisor:
        return student.hall and student.hall.supervisor_id == user.id
    if user.is_teacher:
        return student.hall and student.hall.teacher_id == user.id
    if user.is_parent:
        return student.parent_id == user.id
    return False
