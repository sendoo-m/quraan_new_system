from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from django.utils import timezone
from datetime import date

from accounts.permissions import HallSupervisorRequiredMixin, TeacherRequiredMixin
from students.models import Student
from halls.models import Hall
from .models import DailyFollowUp, StudentEvaluation


# ============================================================
# المتابعة اليومية — مشرف القاعة
# ============================================================
class AddFollowUpView(HallSupervisorRequiredMixin, View):
    template_name = 'evaluations/add_followup.html'

    def get_halls_for_user(self, user):
        if user.is_general_manager:
            return Hall.objects.filter(is_active=True)
        if user.is_general_supervisor:
            return Hall.objects.filter(is_active=True, general_supervisor=user)
        if user.is_hall_supervisor:
            return Hall.objects.filter(is_active=True, supervisor=user)
        return Hall.objects.none()

    def get(self, request):
        halls = self.get_halls_for_user(request.user)
        today = date.today()
        hall_id = request.GET.get('hall')
        existing = None

        if hall_id:
            if halls.filter(pk=hall_id).exists():
                existing = DailyFollowUp.objects.filter(hall_id=hall_id, date=today).first()

        return render(request, self.template_name, {
            'halls': halls,
            'today': today,
            'existing': existing,
            'hall_id': hall_id,
        })

    def post(self, request):
        halls = self.get_halls_for_user(request.user)
        hall_id = request.POST.get('hall')
        homework = request.POST.get('homework', '')
        memorization_task = request.POST.get('memorization_task', '')
        extra_notes = request.POST.get('extra_notes', '')
        today = date.today()

        hall = get_object_or_404(halls, pk=hall_id)

        followup, created = DailyFollowUp.objects.update_or_create(
            hall=hall,
            date=today,
            defaults={
                'homework': homework,
                'memorization_task': memorization_task,
                'extra_notes': extra_notes,
                'created_by': request.user,
            }
        )

        action = 'إضافة' if created else 'تحديث'
        messages.success(request, f'✅ تم {action} المتابعة اليومية لقاعة {hall.name}')
        return redirect('dashboard:hall_supervisor')

class HallFollowUpListView(HallSupervisorRequiredMixin, View):
    template_name = 'evaluations/followup_list.html'

    def get_halls_for_user(self, user):
        if user.is_general_manager:
            return Hall.objects.filter(is_active=True)
        if user.is_general_supervisor:
            return Hall.objects.filter(is_active=True, general_supervisor=user)
        if user.is_hall_supervisor:
            return Hall.objects.filter(is_active=True, supervisor=user)
        return Hall.objects.none()

    def get(self, request, hall_id):
        hall = get_object_or_404(self.get_halls_for_user(request.user), pk=hall_id)
        followups = DailyFollowUp.objects.filter(hall=hall).order_by('-date')[:30]

        return render(request, self.template_name, {
            'hall': hall,
            'followups': followups,
        })

# ============================================================
# تقييم طالب — المعلم
# ============================================================
class EvaluateStudentView(TeacherRequiredMixin, View):
    template_name = 'evaluations/evaluate_student.html'

    def get_allowed_students(self, user):
        if user.is_general_manager:
            return Student.objects.select_related('hall', 'parent', 'age_group')
        if user.is_general_supervisor:
            hall_ids = user.hall_assignments.values_list('hall_id', flat=True)
            return Student.objects.select_related('hall', 'parent', 'age_group').filter(hall_id__in=hall_ids)
        if user.is_teacher:
            return Student.objects.select_related('hall', 'parent', 'age_group').filter(hall__teacher=user)
        return Student.objects.none()

    def get(self, request, student_id):
        student = get_object_or_404(self.get_allowed_students(request.user), pk=student_id)
        today = date.today()
        existing = StudentEvaluation.objects.filter(student=student, date=today).first()

        return render(request, self.template_name, {
            'student': student,
            'existing': existing,
            'rating_choices': StudentEvaluation.RATING_CHOICES,
            'today': today,
        })

    def post(self, request, student_id):
        student = get_object_or_404(self.get_allowed_students(request.user), pk=student_id)
        today = date.today()

        evaluation, created = StudentEvaluation.objects.update_or_create(
            student=student,
            date=today,
            defaults={
                'memorization_rating': request.POST.get('memorization_rating'),
                'memorization_notes': request.POST.get('memorization_notes', ''),
                'behavior_rating': request.POST.get('behavior_rating'),
                'commitment_rating': request.POST.get('commitment_rating'),
                'behavior_notes': request.POST.get('behavior_notes', ''),
                'is_distinguished': request.POST.get('is_distinguished') == 'on',
                'needs_attention': request.POST.get('needs_attention') == 'on',
                'general_notes': request.POST.get('general_notes', ''),
                'teacher': request.user,
            }
        )

        messages.success(request, f'✅ تم تقييم {student.get_full_name()} بنجاح')
        return redirect('dashboard:teacher')


# ============================================================
# تقييم قاعة كاملة — المعلم
# ============================================================
class EvaluateHallView(TeacherRequiredMixin, View):
    template_name = 'evaluations/evaluate_hall.html'

    def get_allowed_halls(self, user):
        if user.is_general_manager:
            return Hall.objects.filter(is_active=True)
        if user.is_general_supervisor:
            hall_ids = user.hall_assignments.values_list('hall_id', flat=True)
            return Hall.objects.filter(is_active=True, id__in=hall_ids)
        if user.is_teacher:
            return Hall.objects.filter(is_active=True, teacher=user)
        return Hall.objects.none()

    def get(self, request, hall_id):
        halls = self.get_allowed_halls(request.user)
        selected_hall = None
        students_data = []
        today = date.today()

        if hall_id:
            selected_hall = get_object_or_404(halls, pk=hall_id)
            students = Student.objects.filter(hall=selected_hall, status='active')
            existing_evals = set(
                StudentEvaluation.objects.filter(
                    date=today, student__in=students
                ).values_list('student_id', flat=True)
            )

            students_data = [{
                'student': s,
                'evaluated': s.id in existing_evals,
            } for s in students]

        return render(request, self.template_name, {
            'halls': halls,
            'selected_hall': selected_hall,
            'students_data': students_data,
            'rating_choices': StudentEvaluation.RATING_CHOICES,
            'today': today,
        })