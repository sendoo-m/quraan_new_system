from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.views import View
from django.db.models import Q
from datetime import date

from accounts.permissions import HallSupervisorRequiredMixin, GeneralSupervisorRequiredMixin
from accounts.models import User
from students.models import Student
from halls.models import Hall
from .models import StudentAttendance, StaffAttendance


# ============================================================
# حضور الطلاب — اختيار القاعة
# ============================================================
class StudentAttendanceView(HallSupervisorRequiredMixin, View):
    def get(self, request):
        if request.user.is_hall_supervisor:
            halls = Hall.objects.filter(supervisor=request.user, is_active=True)
        else:
            halls = Hall.objects.filter(is_active=True)

        context = {
            'halls': halls,
            'today': date.today(),
        }
        return render(request, 'attendance/select_hall.html', context)


# ============================================================
# تسجيل حضور الطلاب
# ============================================================
class TakeAttendanceView(HallSupervisorRequiredMixin, View):
    template_name = 'attendance/take_attendance.html'

    def get(self, request, hall_id):
        hall     = get_object_or_404(Hall, pk=hall_id)
        today    = date.today()
        students = Student.objects.filter(hall=hall, status='active')

        existing = StudentAttendance.objects.filter(
            hall=hall, date=today
        ).values('student_id', 'status')
        existing_map = {r['student_id']: r['status'] for r in existing}

        students_data = [{
            'student': s,
            'status':  existing_map.get(s.id, 'present')
        } for s in students]

        context = {
            'hall':          hall,
            'today':         today,
            'students_data': students_data,
            'already_taken': bool(existing_map),
            'statuses':      StudentAttendance.STATUS_CHOICES,
        }
        return render(request, self.template_name, context)

    def post(self, request, hall_id):
        hall     = get_object_or_404(Hall, pk=hall_id)
        today    = date.today()
        students = Student.objects.filter(hall=hall, status='active')
        saved    = 0

        for student in students:
            status = request.POST.get(f'status_{student.id}', 'absent')
            notes  = request.POST.get(f'notes_{student.id}', '')

            StudentAttendance.objects.update_or_create(
                student=student,
                date=today,
                defaults={
                    'hall':        hall,
                    'status':      status,
                    'notes':       notes,
                    'recorded_by': request.user,
                }
            )
            saved += 1

        messages.success(request, f'✅ تم تسجيل حضور {saved} طالب بنجاح')
        return redirect('attendance:students')


# ============================================================
# حضور الموظفين — قائمة
# ============================================================
class StaffAttendanceView(GeneralSupervisorRequiredMixin, View):
    def get(self, request):
        today        = date.today()
        selected     = request.GET.get('date', str(today))
        role         = request.GET.get('role', '')
        status       = request.GET.get('status', '')
        search       = request.GET.get('q', '')

        records = StaffAttendance.objects.filter(
            date=selected
        ).select_related('staff').order_by('staff__role', 'staff__first_name')

        if role:
            records = records.filter(staff__role=role)
        if status:
            records = records.filter(status=status)
        if search:
            records = records.filter(
                Q(staff__first_name__icontains=search) |
                Q(staff__last_name__icontains=search)
            )

        all_today = StaffAttendance.objects.filter(date=selected)
        stats = {
            'present': all_today.filter(status='present').count(),
            'absent':  all_today.filter(status='absent').count(),
            'late':    all_today.filter(status='late').count(),
            'excused': all_today.filter(status='excused').count(),
        }

        paginator = Paginator(records, 15)
        page      = request.GET.get('page', 1)
        records   = paginator.get_page(page)

        context = {
            'records':        records,
            'total':          paginator.count,
            'stats':          stats,
            'selected_date':  selected,
            'today':          str(today),
            'role_choices':   User.ROLES,
            'status_choices': StaffAttendance.STATUS_CHOICES,
        }
        return render(request, 'attendance/staff_list.html', context)


# ============================================================
# تسجيل حضور الموظفين — جماعي
# ============================================================
class StaffAttendanceMarkView(GeneralSupervisorRequiredMixin, View):
    def get(self, request):
        today    = date.today()
        target   = request.GET.get('date', str(today))
        staff    = User.objects.filter(
            is_active=True,
            role__in=['teacher', 'hall_supervisor']
        ).order_by('role', 'first_name')

        existing = StaffAttendance.objects.filter(
            date=target
        ).values('staff_id', 'status', 'check_in', 'check_out', 'notes', 'id')
        existing_map = {r['staff_id']: r for r in existing}

        staff_data = []
        for user in staff:
            rec = existing_map.get(user.id, {})
            staff_data.append({
                'user':       user,
                'record_id':  rec.get('id'),
                'status':     rec.get('status', 'present'),
                'check_in':   rec.get('check_in', ''),
                'check_out':  rec.get('check_out', ''),
                'notes':      rec.get('notes', ''),
            })

        context = {
            'staff_data':     staff_data,
            'target_date':    target,
            'today':          str(today),
            'status_choices': StaffAttendance.STATUS_CHOICES,
        }
        return render(request, 'attendance/staff_mark.html', context)

    def post(self, request):
        target    = request.POST.get('date', str(date.today()))
        staff_ids = request.POST.getlist('staff_ids')
        saved     = 0

        for uid in staff_ids:
            status    = request.POST.get(f'status_{uid}', 'present')
            check_in  = request.POST.get(f'check_in_{uid}')  or None
            check_out = request.POST.get(f'check_out_{uid}') or None
            notes     = request.POST.get(f'notes_{uid}', '')

            StaffAttendance.objects.update_or_create(
                staff_id=uid,
                date=target,
                defaults={
                    'status':      status,
                    'check_in':    check_in,
                    'check_out':   check_out,
                    'notes':       notes,
                    'recorded_by': request.user,
                }
            )
            saved += 1

        messages.success(request, f'✅ تم حفظ حضور {saved} موظف ليوم {target}')
        return redirect('attendance:staff')


# ============================================================
# تقرير حضور الموظفين — شهري
# ============================================================
class StaffAttendanceReportView(GeneralSupervisorRequiredMixin, View):
    def get(self, request):
        first_day = date.today().replace(day=1)
        from_date = request.GET.get('from', str(first_day))
        to_date   = request.GET.get('to',   str(date.today()))
        role      = request.GET.get('role', '')

        staff = User.objects.filter(
            is_active=True,
            role__in=['teacher', 'hall_supervisor']
        ).order_by('role', 'first_name')

        if role:
            staff = staff.filter(role=role)

        staff_report = []
        for user in staff:
            qs      = StaffAttendance.objects.filter(
                staff=user, date__range=[from_date, to_date]
            )
            present = qs.filter(status='present').count()
            late    = qs.filter(status='late').count()
            absent  = qs.filter(status='absent').count()
            excused = qs.filter(status='excused').count()
            total   = qs.count()

            staff_report.append({
                'user':    user,
                'present': present,
                'late':    late,
                'absent':  absent,
                'excused': excused,
                'total':   total,
                'percent': round((present + late) / total * 100) if total else 0,
            })

        all_records = StaffAttendance.objects.filter(date__range=[from_date, to_date])
        if role:
            all_records = all_records.filter(staff__role=role)

        context = {
            'staff_report':   staff_report,
            'from_date':      from_date,
            'to_date':        to_date,
            'role_choices':   User.ROLES,
            'total_present':  all_records.filter(status='present').count(),
            'total_late':     all_records.filter(status='late').count(),
            'total_absent':   all_records.filter(status='absent').count(),
        }
        return render(request, 'attendance/staff_report.html', context)


# ============================================================
# تقرير حضور الطلاب
# ============================================================
class AttendanceReportView(GeneralSupervisorRequiredMixin, View):
    def get(self, request):
        first_day = date.today().replace(day=1)
        from_date = request.GET.get('from', str(first_day))
        to_date   = request.GET.get('to',   str(date.today()))
        hall_id   = request.GET.get('hall', '')

        attendances = StudentAttendance.objects.filter(
            date__range=[from_date, to_date]
        ).select_related('student', 'hall').order_by('-date')

        if hall_id:
            attendances = attendances.filter(hall_id=hall_id)

        paginator   = Paginator(attendances, 20)
        page        = request.GET.get('page', 1)
        attendances = paginator.get_page(page)

        base_qs = StudentAttendance.objects.filter(date__range=[from_date, to_date])
        if hall_id:
            base_qs = base_qs.filter(hall_id=hall_id)

        context = {
            'attendances': attendances,
            'halls':       Hall.objects.filter(is_active=True),
            'from_date':   from_date,
            'to_date':     to_date,
            'total':       paginator.count,
            'present':     base_qs.filter(status='present').count(),
            'absent':      base_qs.filter(status='absent').count(),
            'late':        base_qs.filter(status='late').count(),
        }
        return render(request, 'attendance/report.html', context)
