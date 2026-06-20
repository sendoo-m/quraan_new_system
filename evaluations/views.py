from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from datetime import date

from accounts.permissions import HallSupervisorRequiredMixin, TeacherRequiredMixin
from students.models import Student
from halls.models import Hall
from .models import DailyFollowUp, StudentEvaluation
from .forms import StudentEvaluationForm, DailyFollowUpForm


# ============================================================
# دوال مساعدة
# ============================================================

def get_halls_for_user(user):
    """
    القاعات المسموحة للمستخدم.
    تدعم النظام الجديد: أكثر من مشرف عام على نفس القاعة عبر hall_assignments.
    وتدعم النظام القديم general_supervisor كـ fallback.
    """
    if not user.is_authenticated:
        return Hall.objects.none()

    base_qs = Hall.objects.filter(is_active=True)

    if user.is_general_manager:
        return base_qs

    if user.is_general_supervisor:
        return base_qs.filter(
            general_supervisor_assignments__supervisor=user
        ).distinct() | base_qs.filter(
            general_supervisor=user
        ).distinct()

    if user.is_hall_supervisor:
        return base_qs.filter(supervisor=user)

    if user.is_teacher:
        return base_qs.filter(teacher=user)

    return Hall.objects.none()


def get_students_for_user(user):
    """
    الطلاب المسموح للمستخدم تقييمهم.
    """
    qs = Student.objects.select_related('hall', 'parent', 'age_group')

    if user.is_general_manager:
        return qs

    if user.is_general_supervisor:
        halls = get_halls_for_user(user)
        return qs.filter(hall__in=halls)

    if user.is_teacher:
        return qs.filter(hall__teacher=user)

    return Student.objects.none()


def get_evaluation_counts(students_data):
    """
    حساب عدد الطلاب الذين تم تقييمهم والذين لم يتم تقييمهم.
    """
    evaluated_count = sum(1 for row in students_data if row.get('evaluated'))
    pending_count = len(students_data) - evaluated_count

    return evaluated_count, pending_count


def add_counts_to_context(context):
    """
    إضافة أرقام التقييم للقالب حتى لا نعدّ داخل template.
    """
    students_data = context.get('students_data', [])
    evaluated_count, pending_count = get_evaluation_counts(students_data)

    context['evaluated_count'] = evaluated_count
    context['pending_count'] = pending_count
    context['students_count'] = len(students_data)

    return context


# ============================================================
# المتابعة اليومية — مشرف القاعة / المشرف العام / المدير
# ============================================================

class AddFollowUpView(HallSupervisorRequiredMixin, View):
    template_name = 'evaluations/add_followup.html'

    def get_halls_for_user(self, user):
        return get_halls_for_user(user)

    def get(self, request):
        halls = self.get_halls_for_user(request.user)
        today = date.today()
        hall_id = request.GET.get('hall')
        existing = None

        if hall_id and halls.filter(pk=hall_id).exists():
            existing = DailyFollowUp.objects.filter(
                hall_id=hall_id,
                date=today
            ).first()

        return render(request, self.template_name, {
            'halls': halls,
            'today': today,
            'existing': existing,
            'hall_id': hall_id,
            'form': DailyFollowUpForm(instance=existing),
        })

    def post(self, request):
        halls = self.get_halls_for_user(request.user)
        hall_id = request.POST.get('hall')
        today = date.today()
        hall = get_object_or_404(halls, pk=hall_id)

        existing = DailyFollowUp.objects.filter(
            hall=hall,
            date=today
        ).first()

        form = DailyFollowUpForm(
            request.POST,
            instance=existing
        )

        if form.is_valid():
            followup = form.save(commit=False)
            followup.hall = hall
            followup.date = today
            followup.created_by = request.user
            followup.save()

            action = 'تحديث' if existing else 'إضافة'

            messages.success(
                request,
                f'✅ تم {action} المتابعة اليومية لقاعة {hall.name}'
            )

            return redirect('dashboard:hall_supervisor')

        return render(request, self.template_name, {
            'halls': halls,
            'today': today,
            'existing': existing,
            'hall_id': hall_id,
            'form': form,
        })


class HallFollowUpListView(HallSupervisorRequiredMixin, View):
    template_name = 'evaluations/followup_list.html'

    def get_halls_for_user(self, user):
        return get_halls_for_user(user)

    def get(self, request, hall_id):
        hall = get_object_or_404(
            self.get_halls_for_user(request.user),
            pk=hall_id
        )

        followups = DailyFollowUp.objects.filter(
            hall=hall
        ).order_by('-date')[:30]

        return render(request, self.template_name, {
            'hall': hall,
            'followups': followups,
        })


# ============================================================
# تقييم طالب فردي — المعلم / المشرف العام / المدير
# ============================================================

class EvaluateStudentView(TeacherRequiredMixin, View):
    template_name = 'evaluations/evaluate_student.html'

    def get_allowed_students(self, user):
        return get_students_for_user(user)

    def get(self, request, student_id):
        student = get_object_or_404(
            self.get_allowed_students(request.user),
            pk=student_id
        )

        today = date.today()

        existing = StudentEvaluation.objects.filter(
            student=student,
            date=today
        ).first()

        return render(request, self.template_name, {
            'student': student,
            'form': StudentEvaluationForm(instance=existing),
            'existing': existing,
            'rating_choices': StudentEvaluation.RATING_CHOICES,
            'today': today,
        })

    def post(self, request, student_id):
        student = get_object_or_404(
            self.get_allowed_students(request.user),
            pk=student_id
        )

        today = date.today()

        existing = StudentEvaluation.objects.filter(
            student=student,
            date=today
        ).first()

        form = StudentEvaluationForm(
            request.POST,
            instance=existing
        )

        if form.is_valid():
            evaluation = form.save(commit=False)
            evaluation.student = student
            evaluation.date = today
            evaluation.teacher = request.user
            evaluation.save()

            messages.success(
                request,
                f'✅ تم تقييم {student.get_full_name()} بنجاح'
            )

            return redirect('dashboard:teacher')

        return render(request, self.template_name, {
            'student': student,
            'form': form,
            'existing': existing,
            'rating_choices': StudentEvaluation.RATING_CHOICES,
            'today': today,
        })


# ============================================================
# تقييم قاعة كاملة دفعة واحدة — المعلم / المشرف العام / المدير
# ============================================================

class EvaluateHallView(TeacherRequiredMixin, View):
    template_name = 'evaluations/evaluate_hall.html'

    def get_allowed_halls(self, user):
        return get_halls_for_user(user)

    def _build_students_data(self, selected_hall, today):
        """
        بناء بيانات الطلاب مع التقييمات الموجودة.
        """
        students = Student.objects.filter(
            hall=selected_hall,
            status='active'
        ).select_related(
            'parent',
            'age_group',
            'hall'
        ).order_by(
            'first_name',
            'last_name'
        )

        existing_evals = {
            evaluation.student_id: evaluation
            for evaluation in StudentEvaluation.objects.filter(
                date=today,
                student__in=students
            )
        }

        students_data = []

        for student in students:
            existing = existing_evals.get(student.id)

            students_data.append({
                'student': student,
                'evaluated': existing is not None,
                'form': StudentEvaluationForm(
                    instance=existing,
                    prefix=f'student_{student.id}'
                ),
            })

        return students_data

    def get(self, request, hall_id):
        halls = self.get_allowed_halls(request.user)
        selected_hall = get_object_or_404(halls, pk=hall_id)
        today = date.today()

        students_data = self._build_students_data(
            selected_hall,
            today
        )

        context = {
            'halls': halls,
            'selected_hall': selected_hall,
            'students_data': students_data,
            'rating_choices': StudentEvaluation.RATING_CHOICES,
            'today': today,
        }

        return render(
            request,
            self.template_name,
            add_counts_to_context(context)
        )

    def post(self, request, hall_id):
        halls = self.get_allowed_halls(request.user)
        selected_hall = get_object_or_404(halls, pk=hall_id)
        today = date.today()

        students = Student.objects.filter(
            hall=selected_hall,
            status='active'
        ).select_related(
            'parent',
            'age_group',
            'hall'
        ).order_by(
            'first_name',
            'last_name'
        )

        saved_count = 0
        errors_count = 0
        students_data = []

        for student in students:
            prefix = f'student_{student.id}'

            existing = StudentEvaluation.objects.filter(
                student=student,
                date=today
            ).first()

            form = StudentEvaluationForm(
                request.POST,
                instance=existing,
                prefix=prefix
            )

            if form.is_valid():
                evaluation = form.save(commit=False)
                evaluation.student = student
                evaluation.date = today
                evaluation.teacher = request.user
                evaluation.save()

                saved_count += 1

                students_data.append({
                    'student': student,
                    'evaluated': True,
                    'form': StudentEvaluationForm(
                        instance=evaluation,
                        prefix=prefix
                    ),
                })
            else:
                errors_count += 1

                students_data.append({
                    'student': student,
                    'evaluated': existing is not None,
                    'form': form,
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

        context = {
            'halls': halls,
            'selected_hall': selected_hall,
            'students_data': students_data,
            'rating_choices': StudentEvaluation.RATING_CHOICES,
            'today': today,
        }

        return render(
            request,
            self.template_name,
            add_counts_to_context(context)
        )


class SelectHallForEvaluationView(TeacherRequiredMixin, View):
    """
    صفحة اختيار القاعة.
    """
    template_name = 'evaluations/select_hall.html'

    def get_allowed_halls(self, user):
        return get_halls_for_user(user)

    def get(self, request):
        halls = self.get_allowed_halls(request.user)

        if halls.count() == 1:
            return redirect(
                'evaluations:evaluate_hall',
                hall_id=halls.first().pk
            )

        return render(request, self.template_name, {
            'halls': halls,
        })


class AllFollowUpsView(HallSupervisorRequiredMixin, View):
    """
    سجل كل المتابعات — للمشرف العام والمدير ومشرف القاعة.
    """
    template_name = 'evaluations/followup_all.html'

    def get_halls_for_user(self, user):
        return get_halls_for_user(user)

    def get(self, request):
        halls = self.get_halls_for_user(request.user)
        hall_id = request.GET.get('hall')

        followups = DailyFollowUp.objects.filter(
            hall__in=halls
        ).select_related(
            'hall',
            'created_by'
        ).order_by(
            '-date'
        )

        if hall_id:
            followups = followups.filter(hall_id=hall_id)

        followups = followups[:60]

        return render(request, self.template_name, {
            'halls': halls,
            'followups': followups,
            'hall_id': hall_id,
        })
    

class EditFollowUpView(HallSupervisorRequiredMixin, View):
    template_name = 'evaluations/edit_followup.html'

    def get_halls_for_user(self, user):
        return get_halls_for_user(user)

    def get_object(self, request, pk):
        return get_object_or_404(
            DailyFollowUp.objects.select_related('hall', 'created_by').filter(
                hall__in=self.get_halls_for_user(request.user)
            ),
            pk=pk
        )

    def get(self, request, pk):
        followup = self.get_object(request, pk)
        form = DailyFollowUpForm(instance=followup)

        return render(request, self.template_name, {
            'followup': followup,
            'form': form,
        })

    def post(self, request, pk):
        followup = self.get_object(request, pk)
        form = DailyFollowUpForm(request.POST, instance=followup)

        if form.is_valid():
            updated = form.save(commit=False)
            updated.hall = followup.hall
            updated.date = followup.date
            updated.created_by = request.user
            updated.save()

            messages.success(
                request,
                f'✅ تم تعديل متابعة قاعة {followup.hall.name} بتاريخ {followup.date}'
            )

            return redirect('evaluations:all_followups')

        return render(request, self.template_name, {
            'followup': followup,
            'form': form,
        })