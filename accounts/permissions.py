from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied


# ====== Mixins للـ Views ======

class GeneralManagerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and \
               self.request.user.is_general_manager

class GeneralSupervisorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and \
               self.request.user.role in ['general_manager', 'general_supervisor']

class HallSupervisorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and \
               self.request.user.role in [
                   'general_manager',
                   'general_supervisor',
                   'hall_supervisor'
               ]

class TeacherRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and \
               self.request.user.role in [
                   'general_manager',
                   'general_supervisor',
                   'teacher'
               ]

class StaffRequiredMixin(UserPassesTestMixin):
    """أي حساب إداري (مش ولي أمر)"""
    def test_func(self):
        return self.request.user.is_authenticated and \
               self.request.user.role != 'parent'

class ParentRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and \
               self.request.user.is_parent
