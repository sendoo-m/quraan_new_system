from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone
from datetime import date

from accounts.permissions import (
    GeneralManagerRequiredMixin,
    GeneralSupervisorRequiredMixin,
    HallSupervisorRequiredMixin,
    TeacherRequiredMixin,
    ParentRequiredMixin,
)
from students.models import Student
from halls.models import Hall
from accounts.models import User
from attendance.models import StudentAttendance, StaffAttendance
from evaluations.models import DailyFollowUp, StudentEvaluation


# ============================================================
# 🔴 مدير عام
# ============================================================
class ManagerDashboard(GeneralManagerRequiredMixin, View):
    def get(self, request):
        today = date.today()
        context = {
            'total_students':    Student.objects.filter(status='active').count(),
            'total_halls':       Hall.objects.filter(is_active=True).count(),
            'total_teachers':    User.objects.filter(role='teacher').count(),
            'total_supervisors': User.objects.filter(role='hall_supervisor').count(),
            'total_parents':     User.objects.filter(role='parent').count(),
            'pending_students':  Student.objects.filter(status='pending').count(),
            'recent_students':   Student.objects.order_by('-registration_date')[:10],
            'halls':             Hall.objects.all(),
        }
        return render(request, 'dashboard/manager.html', context)


# ============================================================
# 🟠 مشرف عام
# ============================================================
class GeneralSupervisorDashboard(GeneralSupervisorRequiredMixin, View):
    def get(self, request):
        today = date.today()
        context = {
            'total_students':      Student.objects.filter(status='active').count(),
            'pending_students':    Student.objects.filter(status='pending'),
            'halls':               Hall.objects.filter(is_active=True),
            'staff_absent_today':  StaffAttendance.objects.filter(
                                       date=today, status='absent'
                                   ).select_related('staff'),
            'teachers':            User.objects.filter(role='teacher'),
            'hall_supervisors':    User.objects.filter(role='hall_supervisor'),
        }
        return render(request, 'dashboard/general_supervisor.html', context)


# ============================================================
# 🟡 مشرف قاعة
# ============================================================
class HallSupervisorDashboard(HallSupervisorRequiredMixin, View):
    def get(self, request):
        today = date.today()
        # القاعات المخصصة لهذا المشرف
        my_halls = Hall.objects.filter(supervisor=request.user)
        context = {
            'my_halls':   my_halls,
            'today':      today,
            'today_name': today.strftime('%A'),
        }
        return render(request, 'dashboard/hall_supervisor.html', context)


# ============================================================
# 🟢 معلم
# ============================================================
class TeacherDashboard(TeacherRequiredMixin, View):
    def get(self, request):
        today = date.today()
        # القاعات المخصصة لهذا المعلم
        my_halls    = Hall.objects.filter(teacher=request.user)
        my_students = Student.objects.filter(
            hall__in=my_halls,
            status='active'
        ).select_related('hall')

        context = {
            'my_halls':       my_halls,
            'my_students':    my_students,
            'total_students': my_students.count(),
            'today':          today,
            # الطلاب اللي لسه مش اتقيّموا النهارده
            'not_evaluated_today': my_students.exclude(
                evaluations__date=today
            ),
        }
        return render(request, 'dashboard/teacher.html', context)


# ============================================================
# 🔵 ولي الأمر
# ============================================================
class ParentDashboard(ParentRequiredMixin, View):
    def get(self, request):
        today    = date.today()
        children = Student.objects.filter(
            parent=request.user
        ).prefetch_related('memorized_surahs', 'evaluations')

        children_data = []
        for child in children:
            last_eval    = child.evaluations.order_by('-date').first()
            today_attend = child.attendances.filter(date=today).first()

            # المتابعات اليومية لقاعة الطالب
            followups = DailyFollowUp.objects.filter(
                hall=child.hall
            ).order_by('-date')[:5] if child.hall else []

            children_data.append({
                'student':       child,
                'last_eval':     last_eval,
                'today_attend':  today_attend,
                'followups':     followups,
                'surahs_count':  child.memorized_surahs.count(),
            })

        context = {
            'children_data': children_data,
            'today':         today,
        }
        return render(request, 'dashboard/parent.html', context)
