from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View

from accounts.permissions import (
    GeneralSupervisorRequiredMixin,
    StaffRequiredMixin,
)
from accounts.models import User
from .models import Hall, Subject, HallSchedule
from .forms import HallForm, HallScheduleForm


class HallListView(StaffRequiredMixin, View):
    def get(self, request):
        halls = Hall.objects.select_related(
            'teacher', 'supervisor'
        ).all()

        context = {
            'halls':      halls,
            'total':      halls.count(),
            'active':     halls.filter(is_active=True).count(),
        }
        return render(request, 'halls/list.html', context)


class HallCreateView(GeneralSupervisorRequiredMixin, View):
    template_name = 'halls/form.html'

    def get(self, request):
        form = HallForm()
        return render(request, self.template_name, {'form': form, 'action': 'إضافة'})

    def post(self, request):
        form = HallForm(request.POST)
        if form.is_valid():
            hall = form.save()
            messages.success(request, f'✅ تم إنشاء قاعة {hall.name} بنجاح')
            return redirect('halls:list')
        return render(request, self.template_name, {'form': form, 'action': 'إضافة'})


class HallDetailView(StaffRequiredMixin, View):
    def get(self, request, pk):
        hall      = get_object_or_404(Hall, pk=pk)
        students  = hall.students.filter(status='active').select_related('parent')
        schedules = hall.schedules.select_related('subject').order_by('day', 'start_time')

        context = {
            'hall':      hall,
            'students':  students,
            'schedules': schedules,
        }
        return render(request, 'halls/detail.html', context)

from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy
from .models import Hall
from .forms import HallForm

class HallUpdateView(UpdateView):
    model         = Hall
    form_class    = HallForm
    template_name = 'halls/form.html'
    success_url   = reverse_lazy('halls:list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['action'] = 'تعديل'
        return ctx

class HallScheduleView(GeneralSupervisorRequiredMixin, View):
    template_name = 'halls/schedule.html'

    def get(self, request, pk):
        hall      = get_object_or_404(Hall, pk=pk)
        schedules = hall.schedules.select_related('subject')
        form      = HallScheduleForm(initial={'hall': hall})

        return render(request, self.template_name, {
            'hall': hall, 'schedules': schedules, 'form': form
        })

    def post(self, request, pk):
        hall = get_object_or_404(Hall, pk=pk)
        form = HallScheduleForm(request.POST)

        if form.is_valid():
            schedule      = form.save(commit=False)
            schedule.hall = hall
            schedule.save()
            messages.success(request, '✅ تم إضافة الحصة للجدول')
            return redirect('halls:schedule', pk=pk)

        schedules = hall.schedules.select_related('subject')
        return render(request, self.template_name, {
            'hall': hall, 'schedules': schedules, 'form': form
        })

# أضفه بعد HallScheduleView مباشرة
class AllSchedulesView(StaffRequiredMixin, View):
    def get(self, request):
        hall_id    = request.GET.get('hall', '')
        DAYS_ORDER = ['saturday','sunday','monday','tuesday','wednesday','thursday','friday']

        halls = Hall.objects.filter(is_active=True).select_related(
            'teacher', 'supervisor', 'age_group'
        )
        if hall_id:
            halls = halls.filter(pk=hall_id)

        # بناء قائمة جاهزة للتيمبلت بدون custom filter
        timetable = []
        COLORS = ['sess-0','sess-1','sess-2','sess-3','sess-4','sess-5']

        for hall in halls:
            days_list = []
            for day_key, day_label in HallSchedule.DAYS:
                sessions = list(
                    HallSchedule.objects.filter(
                        hall=hall, day=day_key
                    ).select_related('subject').order_by('start_time')
                )
                # أضف لون لكل حصة
                for i, s in enumerate(sessions):
                    s.color = COLORS[i % len(COLORS)]
                days_list.append({
                    'key':      day_key,
                    'label':    day_label,
                    'sessions': sessions,
                })

            timetable.append({
                'hall':      hall,
                'days':      days_list,
                'total_sch': sum(len(d['sessions']) for d in days_list),
            })

        context = {
            'timetable':     timetable,
            'all_halls':     Hall.objects.filter(is_active=True),
            'selected_hall': hall_id,
        }
        return render(request, 'halls/all_schedules.html', context)


from .models import Hall, Subject, HallSchedule
from .forms import HallForm, HallScheduleForm, SubjectForm


# ============================================================
# المواد الدراسية — CRUD
# ============================================================
class SubjectListView(GeneralSupervisorRequiredMixin, View):
    def get(self, request):
        subjects = Subject.objects.all()
        context  = {
            'subjects': subjects,
            'total':    subjects.count(),
            'active':   subjects.filter(is_active=True).count(),
        }
        return render(request, 'halls/subjects/list.html', context)


class SubjectCreateView(GeneralSupervisorRequiredMixin, View):
    template_name = 'halls/subjects/form.html'

    def get(self, request):
        form = SubjectForm()
        return render(request, self.template_name, {
            'form': form, 'action': 'إضافة'
        })

    def post(self, request):
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save()
            messages.success(request, f'✅ تم إضافة مادة {subject.name} بنجاح')
            return redirect('halls:subjects')
        return render(request, self.template_name, {
            'form': form, 'action': 'إضافة'
        })


class SubjectUpdateView(GeneralSupervisorRequiredMixin, View):
    template_name = 'halls/subjects/form.html'

    def get(self, request, pk):
        subject = get_object_or_404(Subject, pk=pk)
        form    = SubjectForm(instance=subject)
        return render(request, self.template_name, {
            'form': form, 'action': 'تعديل', 'subject': subject
        })

    def post(self, request, pk):
        subject = get_object_or_404(Subject, pk=pk)
        form    = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ تم تعديل مادة {subject.name} بنجاح')
            return redirect('halls:subjects')
        return render(request, self.template_name, {
            'form': form, 'action': 'تعديل', 'subject': subject
        })


class SubjectDeleteView(GeneralSupervisorRequiredMixin, View):
    def post(self, request, pk):
        subject = get_object_or_404(Subject, pk=pk)
        name    = subject.name

        # تحقق إن المادة مش مستخدمة في جداول
        if subject.hallschedule_set.exists():
            messages.error(
                request,
                f'❌ لا يمكن حذف "{name}" — مستخدمة في جداول القاعات'
            )
        else:
            subject.delete()
            messages.success(request, f'✅ تم حذف مادة {name}')

        return redirect('halls:subjects')
