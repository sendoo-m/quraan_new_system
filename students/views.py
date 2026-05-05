from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.db.models import Q
from django.core.paginator import Paginator

from accounts.permissions import (
    StaffRequiredMixin,
    GeneralSupervisorRequiredMixin,
    user_can_access_student,
)
from accounts.models import User, SiteSettings
from halls.models import Hall
from .models import Student, AgeGroup
from .forms import (
    StudentRegistrationForm,
    TransferStudentForm,
    StudentUpdateForm,
    ParentRegisterForm,
)
from .utils import auto_assign_hall, transfer_student


class StudentListView(StaffRequiredMixin, View):
    def get_base_queryset(self, request):
        user = request.user
        qs = Student.objects.select_related(
            'parent', 'hall', 'age_group'
        ).prefetch_related('memorized_surahs')

        if user.is_general_manager:
            return qs

        if user.is_general_supervisor:
            hall_ids = user.hall_assignments.values_list('hall_id', flat=True)
            return qs.filter(hall_id__in=hall_ids)

        if user.is_hall_supervisor:
            return qs.filter(hall__supervisor=user)

        if user.is_teacher:
            return qs.filter(hall__teacher=user)

        return qs.none()

    def get(self, request):
        students = self.get_base_queryset(request)

        status = request.GET.get('status', '')
        age_group = request.GET.get('age_group', '')
        hall_id = request.GET.get('hall', '')
        search = request.GET.get('q', '')

        if status:
            students = students.filter(status=status)
        if age_group:
            students = students.filter(age_group__id=age_group)
        if hall_id:
            students = students.filter(hall_id=hall_id)
        if search:
            students = students.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(parent__first_name__icontains=search) |
                Q(parent__last_name__icontains=search) |
                Q(parent__username__icontains=search)
            )

        paginator = Paginator(students, 10)
        page = request.GET.get('page', 1)
        students = paginator.get_page(page)

        halls = Hall.objects.filter(is_active=True)
        if request.user.is_general_supervisor:
            hall_ids = request.user.hall_assignments.values_list('hall_id', flat=True)
            halls = halls.filter(id__in=hall_ids)
        elif request.user.is_hall_supervisor:
            halls = halls.filter(supervisor=request.user)
        elif request.user.is_teacher:
            halls = halls.filter(teacher=request.user)

        context = {
            'students': students,
            'halls': halls,
            'age_groups': AgeGroup.objects.filter(is_active=True),
            'statuses': Student.STATUS_CHOICES,
            'total': paginator.count,
        }
        return render(request, 'students/list.html', context)


class StudentRegisterView(LoginRequiredMixin, View):
    template_name = 'students/register.html'

    def get(self, request):
        if not (
            request.user.is_parent or
            request.user.is_general_manager or
            request.user.is_general_supervisor
        ):
            messages.error(request, 'ليس لديك صلاحية تسجيل طالب')
            return redirect('dashboard')

        form = StudentRegistrationForm()
        parents = User.objects.filter(role=User.ROLE_PARENT, is_active=True)

        return render(request, self.template_name, {
            'form': form,
            'parents': parents,
        })

    def post(self, request):
        form = StudentRegistrationForm(request.POST, request.FILES)
        parents = User.objects.filter(role=User.ROLE_PARENT, is_active=True)

        if form.is_valid():
            student = form.save(commit=False)

            if request.user.is_parent:
                student.parent = request.user
            else:
                parent_id = request.POST.get('parent_id')
                if not parent_id:
                    messages.error(request, 'يجب اختيار ولي أمر')
                    return render(request, self.template_name, {'form': form, 'parents': parents})
                student.parent = get_object_or_404(User, id=parent_id, role=User.ROLE_PARENT)

            student.status = Student.STATUS_PENDING
            student.save()
            form.save_m2m()

            settings = SiteSettings.get_settings()
            if settings.auto_assign_halls:
                hall, msg = auto_assign_hall(student)
                if hall:
                    messages.success(request, f'✅ تم تسجيل {student.get_full_name()} وتسكينه في {hall.name}')
                else:
                    messages.warning(request, f'✅ تم التسجيل — ⚠️ {msg}')
            else:
                messages.success(request, f'✅ تم تسجيل {student.get_full_name()} بنجاح')

            return redirect('dashboard:parent' if request.user.is_parent else 'students:list')

        return render(request, self.template_name, {'form': form, 'parents': parents})


class StudentDetailView(LoginRequiredMixin, View):
    def get(self, request, pk):
        student = get_object_or_404(Student, pk=pk)

        if not user_can_access_student(request.user, student):
            messages.error(request, 'ليس لديك صلاحية عرض هذا الطالب')
            return redirect('dashboard')

        from evaluations.models import StudentEvaluation, DailyFollowUp
        from attendance.models import StudentAttendance

        context = {
            'student': student,
            'evaluations': StudentEvaluation.objects.filter(student=student).order_by('-date')[:10],
            'attendances': StudentAttendance.objects.filter(student=student).order_by('-date')[:20],
            'followups': DailyFollowUp.objects.filter(
                hall=student.hall
            ).order_by('-date')[:10] if student.hall else [],
            'surahs': student.memorized_surahs.all(),
        }
        return render(request, 'students/detail.html', context)


class AssignHallView(GeneralSupervisorRequiredMixin, View):
    def post(self, request, pk):
        student = get_object_or_404(Student, pk=pk)

        if not user_can_access_student(request.user, student):
            messages.error(request, 'ليس لديك صلاحية تسكين هذا الطالب')
            return redirect('students:list')

        hall, msg = auto_assign_hall(student)

        if hall:
            messages.success(request, f'✅ {msg}')
        else:
            messages.warning(request, f'⚠️ {msg}')

        return redirect('students:list')


class TransferStudentView(GeneralSupervisorRequiredMixin, View):
    template_name = 'students/transfer.html'

    def get(self, request, pk):
        student = get_object_or_404(Student, pk=pk)

        if not user_can_access_student(request.user, student):
            messages.error(request, 'ليس لديك صلاحية نقل هذا الطالب')
            return redirect('students:list')

        form = TransferStudentForm(student=student)
        return render(request, self.template_name, {'student': student, 'form': form})

    def post(self, request, pk):
        student = get_object_or_404(Student, pk=pk)

        if not user_can_access_student(request.user, student):
            messages.error(request, 'ليس لديك صلاحية نقل هذا الطالب')
            return redirect('students:list')

        form = TransferStudentForm(student=student, data=request.POST)

        if form.is_valid():
            new_hall = form.cleaned_data['new_hall']
            success, msg = transfer_student(student, new_hall)

            if success:
                messages.success(request, f'✅ {msg}')
                return redirect('students:list')
            messages.error(request, f'❌ {msg}')

        return render(request, self.template_name, {'student': student, 'form': form})


class StudentUpdateView(GeneralSupervisorRequiredMixin, View):
    template_name = 'students/update.html'

    def get(self, request, pk):
        student = get_object_or_404(Student, pk=pk)

        if not user_can_access_student(request.user, student):
            messages.error(request, 'ليس لديك صلاحية تعديل هذا الطالب')
            return redirect('students:list')

        form = StudentUpdateForm(instance=student)
        return render(request, self.template_name, {
            'student': student,
            'form': form
        })

    def post(self, request, pk):
        student = get_object_or_404(Student, pk=pk)

        if not user_can_access_student(request.user, student):
            messages.error(request, 'ليس لديك صلاحية تعديل هذا الطالب')
            return redirect('students:list')

        form = StudentUpdateForm(request.POST, request.FILES, instance=student)

        if form.is_valid():
            form.save()
            messages.success(request, f'✅ تم تعديل بيانات {student.get_full_name()} بنجاح')
            return redirect('students:detail', pk=pk)

        return render(request, self.template_name, {
            'student': student,
            'form': form
        })


class PublicRegisterView(View):
    template_name = 'students/public_register.html'

    def get(self, request):
        if request.user.is_authenticated and not request.user.is_parent:
            return redirect('dashboard')

        settings = SiteSettings.get_settings()
        if not settings.allow_registration:
            return render(request, 'students/registration_closed.html')

        parent_form = ParentRegisterForm()
        student_form = StudentRegistrationForm()

        return render(request, self.template_name, {
            'parent_form': parent_form,
            'student_form': student_form,
        })

    def post(self, request):
        settings = SiteSettings.get_settings()

        if not settings.allow_registration:
            messages.error(request, '❌ التسجيل مغلق حالياً')
            return redirect('home')

        parent_form = ParentRegisterForm(request.POST)
        student_form = StudentRegistrationForm(request.POST, request.FILES)

        if parent_form.is_valid() and student_form.is_valid():
            parent = parent_form.save(commit=False)
            parent.role = User.ROLE_PARENT
            parent.set_password(parent_form.cleaned_data['password'])
            parent.save()

            student = student_form.save(commit=False)
            student.parent = parent
            student.status = Student.STATUS_PENDING
            student.save()
            student_form.save_m2m()

            if settings.auto_assign_halls:
                auto_assign_hall(student)

            from django.contrib.auth import login
            login(request, parent)
            messages.success(
                request,
                f'🎉 مرحباً {parent.get_full_name()}! تم تسجيل {student.get_full_name()} بنجاح'
            )
            return redirect('dashboard:parent')

        return render(request, self.template_name, {
            'parent_form': parent_form,
            'student_form': student_form,
        })

# from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib.auth.mixins import LoginRequiredMixin
# from django.contrib import messages
# from django.views import View
# from django.db.models import Q

# from accounts.permissions import (
#     StaffRequiredMixin,
#     GeneralSupervisorRequiredMixin,
# )
# from accounts.models import User
# from halls.models import Hall
# from .models import Student, AgeGroup          # ← import واحد بس
# from .forms import StudentRegistrationForm, TransferStudentForm, StudentUpdateForm
# from .utils import auto_assign_hall, transfer_student


# # ============================================================
# # قائمة الطلاب — للإدارة
# # ============================================================
# class StudentListView(StaffRequiredMixin, View):
#     def get(self, request):
#         students = Student.objects.select_related(
#             'parent', 'hall', 'age_group'
#         ).prefetch_related('memorized_surahs')

#         status    = request.GET.get('status', '')
#         age_group = request.GET.get('age_group', '')
#         hall_id   = request.GET.get('hall', '')
#         search    = request.GET.get('q', '')

#         if status:
#             students = students.filter(status=status)
#         if age_group:
#             students = students.filter(age_group__id=age_group)
#         if hall_id:
#             students = students.filter(hall_id=hall_id)
#         if search:
#             students = students.filter(
#                 Q(first_name__icontains=search) |
#                 Q(last_name__icontains=search)  |
#                 Q(parent__first_name__icontains=search)
#             )

#         context = {
#             'students':   students,
#             'halls':      Hall.objects.filter(is_active=True),
#             'age_groups': AgeGroup.objects.filter(is_active=True),
#             'statuses':   Student.STATUS_CHOICES,
#             'total':      students.count(),
#         }
#         return render(request, 'students/list.html', context)


# # ============================================================
# # تسجيل طالب جديد
# # ============================================================
# class StudentRegisterView(LoginRequiredMixin, View):
#     template_name = 'students/register.html'

#     def get(self, request):
#         if not (request.user.is_parent or request.user.is_general_manager
#                 or request.user.is_general_supervisor):
#             messages.error(request, 'ليس لديك صلاحية تسجيل طالب')
#             return redirect('dashboard')

#         form = StudentRegistrationForm()
#         return render(request, self.template_name, {'form': form})

#     def post(self, request):
#         form = StudentRegistrationForm(request.POST, request.FILES)
#         if form.is_valid():
#             student = form.save(commit=False)

#             if request.user.is_parent:
#                 student.parent = request.user
#             else:
#                 parent_id = request.POST.get('parent_id')
#                 if parent_id:
#                     student.parent = get_object_or_404(User, id=parent_id, role='parent')

#             student.status = Student.STATUS_PENDING
#             student.save()
#             form.save_m2m()

#             hall, msg = auto_assign_hall(student)
#             if hall:
#                 messages.success(request, f'✅ تم تسجيل {student.get_full_name()} وتسكينه في {hall.name}')
#             else:
#                 messages.warning(request, f'✅ تم التسجيل — ⚠️ {msg}')

#             return redirect('dashboard:parent' if request.user.is_parent else 'students:list')

#         return render(request, self.template_name, {'form': form})


# # ============================================================
# # تفاصيل الطالب
# # ============================================================
# class StudentDetailView(LoginRequiredMixin, View):
#     def get(self, request, pk):
#         student = get_object_or_404(Student, pk=pk)

#         if request.user.is_parent and student.parent != request.user:
#             messages.error(request, 'ليس لديك صلاحية عرض هذا الطالب')
#             return redirect('dashboard')

#         from evaluations.models import StudentEvaluation, DailyFollowUp
#         from attendance.models import StudentAttendance

#         context = {
#             'student':     student,
#             'evaluations': StudentEvaluation.objects.filter(student=student).order_by('-date')[:10],
#             'attendances': StudentAttendance.objects.filter(student=student).order_by('-date')[:20],
#             'followups':   DailyFollowUp.objects.filter(
#                                hall=student.hall
#                            ).order_by('-date')[:10] if student.hall else [],
#             'surahs':      student.memorized_surahs.all(),
#         }
#         return render(request, 'students/detail.html', context)


# # ============================================================
# # تسكين يدوي
# # ============================================================
# class AssignHallView(GeneralSupervisorRequiredMixin, View):
#     def post(self, request, pk):
#         student   = get_object_or_404(Student, pk=pk)
#         hall, msg = auto_assign_hall(student)

#         if hall:
#             messages.success(request, f'✅ {msg}')
#         else:
#             messages.warning(request, f'⚠️ {msg}')

#         return redirect('students:list')


# # ============================================================
# # نقل الطالب
# # ============================================================
# class TransferStudentView(GeneralSupervisorRequiredMixin, View):
#     template_name = 'students/transfer.html'

#     def get(self, request, pk):
#         student = get_object_or_404(Student, pk=pk)
#         form    = TransferStudentForm(student=student)
#         return render(request, self.template_name, {'student': student, 'form': form})

#     def post(self, request, pk):
#         student = get_object_or_404(Student, pk=pk)
#         form    = TransferStudentForm(student=student, data=request.POST)

#         if form.is_valid():
#             new_hall     = form.cleaned_data['new_hall']
#             success, msg = transfer_student(student, new_hall)

#             if success:
#                 messages.success(request, f'✅ {msg}')
#                 return redirect('students:list')
#             else:
#                 messages.error(request, f'❌ {msg}')

#         return render(request, self.template_name, {'student': student, 'form': form})

# from django.core.paginator import Paginator

# class StudentListView(StaffRequiredMixin, View):
#     def get(self, request):
#         students = Student.objects.select_related(
#             'parent', 'hall', 'age_group'
#         ).prefetch_related('memorized_surahs')

#         status    = request.GET.get('status', '')
#         age_group = request.GET.get('age_group', '')
#         hall_id   = request.GET.get('hall', '')
#         search    = request.GET.get('q', '')

#         if status:
#             students = students.filter(status=status)
#         if age_group:
#             students = students.filter(age_group__id=age_group)
#         if hall_id:
#             students = students.filter(hall_id=hall_id)
#         if search:
#             students = students.filter(
#                 Q(first_name__icontains=search) |
#                 Q(last_name__icontains=search)  |
#                 Q(parent__first_name__icontains=search)
#             )

#         # Pagination ✅
#         paginator = Paginator(students, 10)  # 15 طالب لكل صفحة
#         page      = request.GET.get('page', 1)
#         students  = paginator.get_page(page)

#         context = {
#             'students':   students,
#             'halls':      Hall.objects.filter(is_active=True),
#             'age_groups': AgeGroup.objects.filter(is_active=True),
#             'statuses':   Student.STATUS_CHOICES,
#             'total':      paginator.count,
#         }
#         return render(request, 'students/list.html', context)

# # ============================================================
# # تعديل بيانات الطالب
# # ============================================================
# class StudentUpdateView(GeneralSupervisorRequiredMixin, View):
#     template_name = 'students/update.html'

#     def get(self, request, pk):
#         student = get_object_or_404(Student, pk=pk)
#         form    = StudentUpdateForm(instance=student)
#         return render(request, self.template_name, {
#             'student': student,
#             'form':    form
#         })

#     def post(self, request, pk):
#         student = get_object_or_404(Student, pk=pk)
#         form    = StudentUpdateForm(request.POST, request.FILES, instance=student)

#         if form.is_valid():
#             form.save()
#             messages.success(request, f'✅ تم تعديل بيانات {student.get_full_name()} بنجاح')
#             return redirect('students:detail', pk=pk)

#         return render(request, self.template_name, {
#             'student': student,
#             'form':    form
#         })


# class PublicRegisterView(View):
#     """صفحة التسجيل العامة — لا تحتاج تسجيل دخول"""
#     template_name = 'students/public_register.html'

#     def get(self, request):
#         # لو مسجل دخول ومش ولي أمر — وجّهه للداش بورد
#         if request.user.is_authenticated and not request.user.is_parent:
#             return redirect('dashboard')

#         from accounts.models import SiteSettings
#         settings = SiteSettings.get_settings()

#         # لو التسجيل مغلق
#         if not settings.allow_registration:
#             return render(request, 'students/registration_closed.html')

#         from .forms import ParentRegisterForm, StudentRegistrationForm
#         parent_form  = ParentRegisterForm()
#         student_form = StudentRegistrationForm()
#         return render(request, self.template_name, {
#             'parent_form':  parent_form,
#             'student_form': student_form,
#         })

#     def post(self, request):
#         from accounts.models import SiteSettings
#         settings = SiteSettings.get_settings()

#         if not settings.allow_registration:
#             messages.error(request, '❌ التسجيل مغلق حالياً')
#             return redirect('home')

#         from .forms import ParentRegisterForm, StudentRegistrationForm
#         parent_form  = ParentRegisterForm(request.POST)
#         student_form = StudentRegistrationForm(request.POST, request.FILES)

#         if parent_form.is_valid() and student_form.is_valid():
#             # إنشاء حساب ولي الأمر
#             parent = parent_form.save(commit=False)
#             parent.role = 'parent'
#             parent.set_password(parent_form.cleaned_data['password'])
#             parent.save()

#             # إنشاء الطالب وربطه بولي الأمر
#             student = student_form.save(commit=False)
#             student.parent = parent
#             student.status = Student.STATUS_PENDING
#             student.save()
#             student_form.save_m2m()

#             # التسكين التلقائي لو مفعّل
#             if settings.auto_assign_halls:
#                 hall, msg = auto_assign_hall(student)

#             # تسجيل دخول ولي الأمر تلقائياً
#             from django.contrib.auth import login
#             login(request, parent)
#             messages.success(
#                 request,
#                 f'🎉 مرحباً {parent.get_full_name()}! تم تسجيل {student.get_full_name()} بنجاح'
#             )
#             return redirect('dashboard:parent')

#         return render(request, self.template_name, {
#             'parent_form':  parent_form,
#             'student_form': student_form,
#         })
