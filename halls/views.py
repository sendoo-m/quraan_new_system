from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy

from accounts.permissions import (
    GeneralSupervisorRequiredMixin,
    StaffRequiredMixin,
    user_can_access_hall,
)
from .models import Hall, Subject, HallSchedule
from .forms import HallForm, HallScheduleForm, SubjectForm

class HallListView(StaffRequiredMixin, View):
    def get_queryset(self, request):
        user = request.user
        qs = Hall.objects.select_related(
            'teacher', 'supervisor', 'general_supervisor', 'age_group'
        )

        if user.is_general_manager:
            return qs
        if user.is_general_supervisor:
            return qs.filter(general_supervisor=user)
        if user.is_hall_supervisor:
            return qs.filter(supervisor=user)
        if user.is_teacher:
            return qs.filter(teacher=user)
        return qs.none()

    def get(self, request):
        halls = self.get_queryset(request)

        context = {
            'halls': halls,
            'total': halls.count(),
            'active': halls.filter(is_active=True).count(),
        }
        return render(request, 'halls/list.html', context)


class HallCreateView(GeneralSupervisorRequiredMixin, View):
    template_name = 'halls/form.html'

    def get(self, request):
        form = HallForm(user=request.user)
        return render(request, self.template_name, {'form': form, 'action': 'إضافة'})

    def post(self, request):
        form = HallForm(request.POST, user=request.user)
        if form.is_valid():
            hall = form.save(commit=False)

            if request.user.is_general_supervisor and not request.user.is_general_manager:
                hall.general_supervisor = request.user

            hall.save()
            messages.success(request, f'✅ تم إنشاء قاعة {hall.name} بنجاح')
            return redirect('halls:list')

        return render(request, self.template_name, {'form': form, 'action': 'إضافة'})
    

class HallDetailView(StaffRequiredMixin, View):
    def get(self, request, pk):
        hall = get_object_or_404(
            Hall.objects.select_related(
                'teacher', 'supervisor', 'general_supervisor', 'age_group'
            ),
            pk=pk
        )

        if not user_can_access_hall(request.user, hall):
            messages.error(request, 'ليس لديك صلاحية عرض هذه القاعة')
            return redirect('halls:list')

        students = hall.students.filter(status='active').select_related('parent')
        schedules = hall.schedules.select_related('subject').order_by('day', 'start_time')

        context = {
            'hall': hall,
            'students': students,
            'schedules': schedules,
        }
        return render(request, 'halls/detail.html', context)

class HallUpdateView(GeneralSupervisorRequiredMixin, UpdateView):
    model = Hall
    form_class = HallForm
    template_name = 'halls/form.html'
    success_url = reverse_lazy('halls:list')

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not user_can_access_hall(request.user, obj):
            messages.error(request, 'ليس لديك صلاحية تعديل هذه القاعة')
            return redirect('halls:list')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        hall = form.save(commit=False)

        if self.request.user.is_general_supervisor and not self.request.user.is_general_manager:
            hall.general_supervisor = self.request.user

        hall.save()
        messages.success(self.request, f'✅ تم تعديل بيانات القاعة {hall.name}')
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['action'] = 'تعديل'
        return ctx
    
class HallScheduleView(GeneralSupervisorRequiredMixin, View):
    template_name = 'halls/schedule.html'

    def get(self, request, pk):
        hall = get_object_or_404(Hall, pk=pk)

        if not user_can_access_hall(request.user, hall):
            messages.error(request, 'ليس لديك صلاحية إدارة جدول هذه القاعة')
            return redirect('halls:list')

        schedules = hall.schedules.select_related('subject')
        form = HallScheduleForm(hall=hall)

        return render(request, self.template_name, {
            'hall': hall,
            'schedules': schedules,
            'form': form
        })

    def post(self, request, pk):
        hall = get_object_or_404(Hall, pk=pk)

        if not user_can_access_hall(request.user, hall):
            messages.error(request, 'ليس لديك صلاحية إدارة جدول هذه القاعة')
            return redirect('halls:list')

        form = HallScheduleForm(request.POST, hall=hall)

        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.hall = hall
            schedule.save()
            messages.success(request, '✅ تم إضافة الحصة للجدول')
            return redirect('halls:schedule', pk=pk)

        schedules = hall.schedules.select_related('subject')
        return render(request, self.template_name, {
            'hall': hall,
            'schedules': schedules,
            'form': form
        })


class AllSchedulesView(StaffRequiredMixin, View):
    def get_allowed_halls(self, request):
        user = request.user
        qs = Hall.objects.filter(is_active=True).select_related(
            'teacher', 'supervisor', 'general_supervisor', 'age_group'
        )

        if user.is_general_manager:
            return qs
        if user.is_general_supervisor:
            return qs.filter(general_supervisor=user)
        if user.is_hall_supervisor:
            return qs.filter(supervisor=user)
        if user.is_teacher:
            return qs.filter(teacher=user)
        return qs.none()

    def get(self, request):
        hall_id = request.GET.get('hall', '')
        halls = self.get_allowed_halls(request)

        if hall_id:
            halls = halls.filter(pk=hall_id)

        schedules = HallSchedule.objects.filter(hall__in=halls).select_related('hall', 'subject').order_by(
            'hall__name', 'day', 'start_time'
        )

        schedule_map = {}
        for item in schedules:
            schedule_map.setdefault(item.hall_id, {}).setdefault(item.day, []).append(item)

        timetable = []
        colors = ['sess-0', 'sess-1', 'sess-2', 'sess-3', 'sess-4', 'sess-5']

        for hall in halls:
            days_list = []
            for day_key, day_label in HallSchedule.DAYS:
                sessions = schedule_map.get(hall.id, {}).get(day_key, [])
                for i, session in enumerate(sessions):
                    session.color = colors[i % len(colors)]
                days_list.append({
                    'key': day_key,
                    'label': day_label,
                    'sessions': sessions,
                })

            timetable.append({
                'hall': hall,
                'days': days_list,
                'total_sch': sum(len(d['sessions']) for d in days_list),
            })

        context = {
            'timetable': timetable,
            'all_halls': self.get_allowed_halls(request),
            'selected_hall': hall_id,
        }
        return render(request, 'halls/all_schedules.html', context)


class SubjectListView(GeneralSupervisorRequiredMixin, View):
    def get(self, request):
        subjects = Subject.objects.all()
        context = {
            'subjects': subjects,
            'total': subjects.count(),
            'active': subjects.filter(is_active=True).count(),
        }
        return render(request, 'halls/subjects/list.html', context)


class SubjectCreateView(GeneralSupervisorRequiredMixin, View):
    template_name = 'halls/subjects/form.html'

    def get(self, request):
        form = SubjectForm()
        return render(request, self.template_name, {
            'form': form,
            'action': 'إضافة'
        })

    def post(self, request):
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save()
            messages.success(request, f'✅ تم إضافة مادة {subject.name} بنجاح')
            return redirect('halls:subjects')
        return render(request, self.template_name, {
            'form': form,
            'action': 'إضافة'
        })


class SubjectUpdateView(GeneralSupervisorRequiredMixin, View):
    template_name = 'halls/subjects/form.html'

    def get(self, request, pk):
        subject = get_object_or_404(Subject, pk=pk)
        form = SubjectForm(instance=subject)
        return render(request, self.template_name, {
            'form': form,
            'action': 'تعديل',
            'subject': subject
        })

    def post(self, request, pk):
        subject = get_object_or_404(Subject, pk=pk)
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ تم تعديل مادة {subject.name} بنجاح')
            return redirect('halls:subjects')
        return render(request, self.template_name, {
            'form': form,
            'action': 'تعديل',
            'subject': subject
        })


class SubjectDeleteView(GeneralSupervisorRequiredMixin, View):
    def post(self, request, pk):
        subject = get_object_or_404(Subject, pk=pk)
        name = subject.name

        if subject.hallschedule_set.exists():
            messages.error(
                request,
                f'❌ لا يمكن حذف "{name}" — مستخدمة في جداول القاعات'
            )
        else:
            subject.delete()
            messages.success(request, f'✅ تم حذف مادة {name}')

        return redirect('halls:subjects')
