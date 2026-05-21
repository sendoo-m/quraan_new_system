from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from django.db.models import Count, Q, F
from datetime import date

from accounts.permissions import (
    GeneralManagerRequiredMixin,
    GeneralSupervisorRequiredMixin,
    HallSupervisorRequiredMixin,
    TeacherRequiredMixin,
    ParentRequiredMixin,
)
from accounts.forms_settings import ParentProfileForm
from students.models import Student
from students.forms import StudentUpdateForm
from halls.models import Hall
from accounts.models import User
from attendance.models import StudentAttendance, StaffAttendance
from evaluations.models import DailyFollowUp, StudentEvaluation


# ============================================================
# 🔴 مدير عام
# ============================================================
class ManagerDashboard(GeneralManagerRequiredMixin, View):
    def get(self, request):
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
            'total_students':     Student.objects.filter(status='active').count(),
            'pending_students':   Student.objects.filter(status='pending'),
            'halls':              Hall.objects.filter(is_active=True),
            'staff_absent_today': StaffAttendance.objects.filter(
                                      date=today, status='absent'
                                  ).select_related('staff'),
            'teachers':           User.objects.filter(role='teacher'),
            'hall_supervisors':   User.objects.filter(role='hall_supervisor'),
        }
        return render(request, 'dashboard/general_supervisor.html', context)


# ============================================================
# 🟡 مشرف قاعة
# ============================================================
class HallSupervisorDashboard(HallSupervisorRequiredMixin, View):
    def get(self, request):
        today    = date.today()
        my_halls = Hall.objects.filter(supervisor=request.user)
        context  = {
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
        today       = date.today()
        my_halls    = Hall.objects.filter(teacher=request.user)
        my_students = Student.objects.filter(
            hall__in=my_halls,
            status='active'
        ).select_related('hall')

        context = {
            'my_halls':            my_halls,
            'my_students':         my_students,
            'total_students':      my_students.count(),
            'today':               today,
            'not_evaluated_today': my_students.exclude(evaluations__date=today),
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
            followups    = DailyFollowUp.objects.filter(
                               hall=child.hall
                           ).order_by('-date')[:5] if child.hall else []

            children_data.append({
                'student':      child,
                'last_eval':    last_eval,
                'today_attend': today_attend,
                'followups':    followups,
                'surahs_count': child.memorized_surahs.count(),
            })

        context = {
            'children_data': children_data,
            'children':      children,
            'today':         today,
        }
        return render(request, 'dashboard/parent.html', context)


# ============================================================
# 📊 تقرير طالب لولي الأمر
# ============================================================
class ParentStudentReportView(ParentRequiredMixin, View):
    def get(self, request, student_id):
        child = get_object_or_404(Student, pk=student_id, parent=request.user)

        all_attendance = child.attendances.all()
        attend_stats   = {
            'present': all_attendance.filter(status='present').count(),
            'absent':  all_attendance.filter(status='absent').count(),
            'late':    all_attendance.filter(status='late').count(),
            'excused': all_attendance.filter(status='excused').count(),
            'total':   all_attendance.count(),
        }

        all_evals  = child.evaluations.all()
        eval_stats = {
            'total':             all_evals.count(),
            'excellent':         all_evals.filter(memorization_rating='excellent').count(),
            'good':              all_evals.filter(memorization_rating='good').count(),
            'average':           all_evals.filter(memorization_rating='average').count(),
            'weak':              all_evals.filter(memorization_rating='weak').count(),
            'distinguished':     all_evals.filter(is_distinguished=True).count(),
            'needs_attention':   all_evals.filter(needs_attention=True).count(),
        }

        recent_evals = all_evals.select_related('teacher').order_by('-date')[:20]

        followups = DailyFollowUp.objects.filter(
            hall=child.hall
        ).order_by('-date') if child.hall else []

        context = {
            'child':        child,
            'attend_stats': attend_stats,
            'eval_stats':   eval_stats,
            'recent_evals': recent_evals,
            'followups':    followups[:10],
            'surahs_count': child.memorized_surahs.count(),
        }
        return render(request, 'dashboard/student_report.html', context)


# ============================================================
# 👤 ملف ولي الأمر الشخصي
# ============================================================
class ParentProfileView(ParentRequiredMixin, View):
    template_name = 'dashboard/parent_profile.html'

    def get(self, request):
        form = ParentProfileForm(instance=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = ParentProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ تم تحديث بياناتك بنجاح')
            return redirect('dashboard:parent_profile')
        return render(request, self.template_name, {'form': form})
    
from students.forms import ParentStudentUpdateForm


# ============================================================
# ✏️ تعديل بيانات الطالب من ولي الأمر
# ============================================================

class ParentStudentUpdateView(View):
    template_name = 'dashboard/parent_student_edit.html'

    def get_available_halls(self, child):
        student_age = child.calculate_age()
        return Hall.objects.filter(
            is_active=True,
            age_group__is_active=True,
            age_group__min_age__lte=student_age,
            age_group__max_age__gte=student_age,
        ).annotate(
            current_students_count=Count('students')
        ).filter(
            current_students_count__lt=F('max_students')
        ).select_related('age_group')

    def get(self, request, student_id):
        child = get_object_or_404(Student, pk=student_id, parent=request.user)
        form = StudentUpdateForm(instance=child)
        available_halls = self.get_available_halls(child)

        return render(request, self.template_name, {
            'child': child,
            'form': form,
            'available_halls': available_halls,
        })

    def post(self, request, student_id):
        child = get_object_or_404(Student, pk=student_id, parent=request.user)
        form = StudentUpdateForm(request.POST, instance=child)
        available_halls = self.get_available_halls(child)

        if form.is_valid():
            student = form.save(commit=False)
            selected_hall_id = request.POST.get('selected_hall')

            if selected_hall_id:
                hall = available_halls.filter(id=selected_hall_id).first()

                if not hall:
                    messages.error(request, '❌ القاعة المختارة غير متاحة أو غير مناسبة لسن الطالب أو ممتلئة')
                    return render(request, self.template_name, {
                        'child': child,
                        'form': form,
                        'available_halls': available_halls,
                    })

                student.hall = hall

            student.save()
            form.save_m2m()

            messages.success(request, '✅ تم حفظ التعديلات بنجاح')
            return redirect('dashboard:parent')

        return render(request, self.template_name, {
            'child': child,
            'form': form,
            'available_halls': available_halls,
        })