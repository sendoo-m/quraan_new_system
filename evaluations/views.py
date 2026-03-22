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

    def get(self, request):
        if request.user.is_hall_supervisor:
            halls = Hall.objects.filter(supervisor=request.user, is_active=True)
        else:
            halls = Hall.objects.filter(is_active=True)

        today     = date.today()
        hall_id   = request.GET.get('hall')
        existing  = None

        if hall_id:
            existing = DailyFollowUp.objects.filter(
                hall_id=hall_id, date=today
            ).first()

        context = {
            'halls':    halls,
            'today':    today,
            'existing': existing,
            'hall_id':  hall_id,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        hall_id           = request.POST.get('hall')
        homework          = request.POST.get('homework', '')
        memorization_task = request.POST.get('memorization_task', '')
        extra_notes       = request.POST.get('extra_notes', '')
        today             = date.today()

        hall = get_object_or_404(Hall, pk=hall_id)

        followup, created = DailyFollowUp.objects.update_or_create(
            hall=hall,
            date=today,
            defaults={
                'homework':           homework,
                'memorization_task':  memorization_task,
                'extra_notes':        extra_notes,
                'created_by':         request.user,
            }
        )

        action = 'إضافة' if created else 'تحديث'
        messages.success(request, f'✅ تم {action} المتابعة اليومية لقاعة {hall.name}')
        return redirect('dashboard:hall_supervisor')


class HallFollowUpListView(HallSupervisorRequiredMixin, View):
    def get(self, request, hall_id):
        hall      = get_object_or_404(Hall, pk=hall_id)
        followups = DailyFollowUp.objects.filter(
            hall=hall
        ).order_by('-date')[:30]

        return render(request, 'evaluations/followup_list.html', {
            'hall': hall, 'followups': followups
        })


# ============================================================
# تقييم طالب — المعلم
# ============================================================
class EvaluateStudentView(TeacherRequiredMixin, View):
    template_name = 'evaluations/evaluate_student.html'

    def get(self, request, student_id):
        student  = get_object_or_404(Student, pk=student_id)
        today    = date.today()
        existing = StudentEvaluation.objects.filter(
            student=student, date=today
        ).first()

        context = {
            'student':        student,
            'existing':       existing,
            'rating_choices': StudentEvaluation.RATING_CHOICES,
            'today':          today,
        }
        return render(request, self.template_name, context)

    def post(self, request, student_id):
        student = get_object_or_404(Student, pk=student_id)
        today   = date.today()

        evaluation, created = StudentEvaluation.objects.update_or_create(
            student=student,
            date=today,
            defaults={
                'memorization_rating': request.POST.get('memorization_rating'),
                'memorization_notes':  request.POST.get('memorization_notes', ''),
                'behavior_rating':     request.POST.get('behavior_rating'),
                'commitment_rating':   request.POST.get('commitment_rating'),
                'behavior_notes':      request.POST.get('behavior_notes', ''),
                'is_distinguished':    request.POST.get('is_distinguished') == 'on',
                'needs_attention':     request.POST.get('needs_attention') == 'on',
                'general_notes':       request.POST.get('general_notes', ''),
                'teacher':             request.user,
            }
        )

        messages.success(
            request,
            f'✅ تم تقييم {student.get_full_name()} بنجاح'
        )
        return redirect('dashboard:teacher')


# ============================================================
# تقييم قاعة كاملة — المعلم
# ============================================================
class EvaluateHallView(TeacherRequiredMixin, View):
    template_name = 'evaluations/evaluate_hall.html'

    def get(self, request, hall_id):
        if request.user.is_teacher:
            halls = Hall.objects.filter(teacher=request.user, is_active=True)
        else:
            halls = Hall.objects.filter(is_active=True)

        selected_hall = None
        students_data = []
        today         = date.today()

        if hall_id and hall_id != 0:
            selected_hall = get_object_or_404(Hall, pk=hall_id)
            students      = Student.objects.filter(
                hall=selected_hall, status='active'
            )
            existing_evals = StudentEvaluation.objects.filter(
                date=today, student__in=students
            ).values_list('student_id', flat=True)

            students_data = [{
                'student':    s,
                'evaluated':  s.id in existing_evals,
            } for s in students]

        context = {
            'halls':          halls,
            'selected_hall':  selected_hall,
            'students_data':  students_data,
            'rating_choices': StudentEvaluation.RATING_CHOICES,
            'today':          today,
        }
        return render(request, self.template_name, context)
