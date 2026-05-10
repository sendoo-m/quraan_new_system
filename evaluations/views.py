from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from django.utils import timezone
from datetime import date

from accounts.permissions import HallSupervisorRequiredMixin, TeacherRequiredMixin
from students.models import Student
from halls.models import Hall
from .models import DailyFollowUp, StudentEvaluation
from .forms import StudentEvaluationForm, DailyFollowUpForm


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

        if hall_id and halls.filter(pk=hall_id).exists():
            existing = DailyFollowUp.objects.filter(hall_id=hall_id, date=today).first()

        return render(request, self.template_name, {
            'halls':    halls,
            'today':    today,
            'existing': existing,
            'hall_id':  hall_id,
            'form':     DailyFollowUpForm(instance=existing),
        })

    def post(self, request):
        halls   = self.get_halls_for_user(request.user)
        hall_id = request.POST.get('hall')
        today   = date.today()
        hall    = get_object_or_404(halls, pk=hall_id)

        existing = DailyFollowUp.objects.filter(hall=hall, date=today).first()
        form = DailyFollowUpForm(request.POST, instance=existing)

        if form.is_valid():
            followup = form.save(commit=False)
            followup.hall       = hall
            followup.date       = today
            followup.created_by = request.user
            followup.save()
            action = 'تحديث' if existing else 'إضافة'
            messages.success(request, f'✅ تم {action} المتابعة اليومية لقاعة {hall.name}')
            return redirect('dashboard:hall_supervisor')

        return render(request, self.template_name, {
            'halls':    halls,
            'today':    today,
            'existing': existing,
            'hall_id':  hall_id,
            'form':     form,
        })


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
        hall      = get_object_or_404(self.get_halls_for_user(request.user), pk=hall_id)
        followups = DailyFollowUp.objects.filter(hall=hall).order_by('-date')[:30]
        return render(request, self.template_name, {'hall': hall, 'followups': followups})


# ============================================================
# تقييم طالب فردي — المعلم
# ============================================================
class EvaluateStudentView(TeacherRequiredMixin, View):
    template_name = 'evaluations/evaluate_student.html'

    def get_allowed_students(self, user):
        qs = Student.objects.select_related('hall', 'parent', 'age_group')
        if user.is_general_manager:
            return qs
        if user.is_general_supervisor:
            hall_ids = user.hall_assignments.values_list('hall_id', flat=True)
            return qs.filter(hall_id__in=hall_ids)
        if user.is_teacher:
            return qs.filter(hall__teacher=user)
        return Student.objects.none()

    def get(self, request, student_id):
        student  = get_object_or_404(self.get_allowed_students(request.user), pk=student_id)
        today    = date.today()
        existing = StudentEvaluation.objects.filter(student=student, date=today).first()
        return render(request, self.template_name, {
            'student':        student,
            'form':           StudentEvaluationForm(instance=existing),
            'existing':       existing,
            'rating_choices': StudentEvaluation.RATING_CHOICES,
            'today':          today,
        })

    def post(self, request, student_id):
        student  = get_object_or_404(self.get_allowed_students(request.user), pk=student_id)
        today    = date.today()
        existing = StudentEvaluation.objects.filter(student=student, date=today).first()
        form     = StudentEvaluationForm(request.POST, instance=existing)

        if form.is_valid():
            evaluation          = form.save(commit=False)
            evaluation.student  = student
            evaluation.date     = today
            evaluation.teacher  = request.user
            evaluation.save()
            messages.success(request, f'✅ تم تقييم {student.get_full_name()} بنجاح')
            return redirect('dashboard:teacher')

        return render(request, self.template_name, {
            'student':        student,
            'form':           form,
            'existing':       existing,
            'rating_choices': StudentEvaluation.RATING_CHOICES,
            'today':          today,
        })


# ============================================================
# تقييم قاعة كاملة دفعة واحدة — المعلم ★
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

    def _build_students_data(self, selected_hall, today):
        """بناء بيانات الطلاب مع التقييمات الموجودة"""
        students = Student.objects.filter(
            hall=selected_hall, status='active'
        ).select_related('parent')

        existing_evals = {
            e.student_id: e
            for e in StudentEvaluation.objects.filter(
                date=today, student__in=students
            )
        }

        return [
            {
                'student':   s,
                'evaluated': s.id in existing_evals,
                'form':      StudentEvaluationForm(
                                 instance=existing_evals.get(s.id),
                                 prefix=f'student_{s.id}'
                             ),
            }
            for s in students
        ]

    def get(self, request, hall_id):
        halls         = self.get_allowed_halls(request.user)
        selected_hall = get_object_or_404(halls, pk=hall_id)
        today         = date.today()

        return render(request, self.template_name, {
            'halls':          halls,
            'selected_hall':  selected_hall,
            'students_data':  self._build_students_data(selected_hall, today),
            'rating_choices': StudentEvaluation.RATING_CHOICES,
            'today':          today,
        })

    def post(self, request, hall_id):
        halls         = self.get_allowed_halls(request.user)
        selected_hall = get_object_or_404(halls, pk=hall_id)
        today         = date.today()

        students = Student.objects.filter(
            hall=selected_hall, status='active'
        )

        saved_count  = 0
        errors_count = 0
        students_data = []

        for student in students:
            prefix   = f'student_{student.id}'
            existing = StudentEvaluation.objects.filter(
                student=student, date=today
            ).first()
            form = StudentEvaluationForm(
                request.POST, instance=existing, prefix=prefix
            )

            if form.is_valid():
                evaluation         = form.save(commit=False)
                evaluation.student = student
                evaluation.date    = today
                evaluation.teacher = request.user
                evaluation.save()
                saved_count += 1
                students_data.append({
                    'student':   student,
                    'evaluated': True,
                    'form':      StudentEvaluationForm(
                                     instance=evaluation,
                                     prefix=prefix
                                 ),
                })
            else:
                errors_count += 1
                students_data.append({
                    'student':   student,
                    'evaluated': existing is not None,
                    'form':      form,
                })

        if errors_count == 0:
            messages.success(
                request,
                f'✅ تم حفظ تقييمات {saved_count} طالب في قاعة {selected_hall.name}'
            )
            return redirect('dashboard:teacher')

        messages.warning(
            request,
            f'⚠️ تم حفظ {saved_count} تقييم — {errors_count} يحتاج مراجعة'
        )
        return render(request, self.template_name, {
            'halls':          halls,
            'selected_hall':  selected_hall,
            'students_data':  students_data,
            'rating_choices': StudentEvaluation.RATING_CHOICES,
            'today':          today,
        })
    
class SelectHallForEvaluationView(TeacherRequiredMixin, View):
    """صفحة اختيار القاعة — للمدير والمشرف العام فقط"""
    template_name = 'evaluations/select_hall.html'

    def get_allowed_halls(self, user):
        if user.is_general_manager:
            return Hall.objects.filter(is_active=True)
        if user.is_general_supervisor:
            hall_ids = user.hall_assignments.values_list('hall_id', flat=True)
            return Hall.objects.filter(is_active=True, id__in=hall_ids)
        if user.is_teacher:
            return Hall.objects.filter(is_active=True, teacher=user)
        return Hall.objects.none()

    def get(self, request):
        halls = self.get_allowed_halls(request.user)

        # لو عنده قاعة واحدة فقط → اذهب مباشرة
        if halls.count() == 1:
            return redirect('evaluations:evaluate_hall', hall_id=halls.first().pk)

        return render(request, self.template_name, {'halls': halls})
    

class AllFollowUpsView(HallSupervisorRequiredMixin, View):
    """سجل كل المتابعات — للمشرف العام والمدير"""
    template_name = 'evaluations/followup_all.html'

    def get_halls_for_user(self, user):
        if user.is_general_manager:
            return Hall.objects.filter(is_active=True)
        if user.is_general_supervisor:
            return Hall.objects.filter(is_active=True, general_supervisor=user)
        if user.is_hall_supervisor:
            return Hall.objects.filter(is_active=True, supervisor=user)
        return Hall.objects.none()

    def get(self, request):
        halls   = self.get_halls_for_user(request.user)
        hall_id = request.GET.get('hall')

        # ← الفلتر أولاً، ثم الـ slice في الأخير
        followups = DailyFollowUp.objects.filter(
            hall__in=halls
        ).select_related('hall', 'created_by').order_by('-date')

        if hall_id:
            followups = followups.filter(hall_id=hall_id)

        followups = followups[:60]  # ← الـ slice بعد كل الفلاتر

        return render(request, self.template_name, {
            'halls':     halls,
            'followups': followups,
            'hall_id':   hall_id,
        })