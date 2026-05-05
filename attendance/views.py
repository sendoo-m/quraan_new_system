from datetime import date, datetime

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from accounts.models import User
from accounts.permissions import HallSupervisorRequiredMixin, GeneralSupervisorRequiredMixin
from halls.models import Hall
from students.models import Student
from .models import StudentAttendance, StaffAttendance


def parse_date(value, default):
    try:
        return datetime.strptime(value, '%Y-%m-%d').date() if value else default
    except (ValueError, TypeError):
        return default


def get_halls_for_user(user):
    if user.is_general_manager:
        return Hall.objects.filter(is_active=True)
    if user.is_general_supervisor:
        return Hall.objects.filter(is_active=True, general_supervisor=user)
    if user.is_hall_supervisor:
        return Hall.objects.filter(is_active=True, supervisor=user)
    return Hall.objects.none()


class StudentAttendanceView(HallSupervisorRequiredMixin, View):
    def get(self, request):
        context = {
            'halls': get_halls_for_user(request.user),
            'today': date.today(),
        }
        return render(request, 'attendance/select_hall.html', context)


class TakeAttendanceView(HallSupervisorRequiredMixin, View):
    template_name = 'attendance/take_attendance.html'

    def get(self, request, hall_id):
        hall = get_object_or_404(get_halls_for_user(request.user), pk=hall_id)
        today = date.today()
        students = Student.objects.filter(hall=hall, status='active').select_related('parent', 'age_group')

        existing = StudentAttendance.objects.filter(
            hall=hall,
            date=today
        ).values('student_id', 'status', 'notes', 'arrival_time')

        existing_map = {r['student_id']: r for r in existing}

        students_data = []
        for student in students:
            rec = existing_map.get(student.id, {})
            students_data.append({
                'student': student,
                'status': rec.get('status', StudentAttendance.STATUS_PRESENT),
                'notes': rec.get('notes', ''),
                'arrival_time': rec.get('arrival_time', ''),
            })

        context = {
            'hall': hall,
            'today': today,
            'students_data': students_data,
            'already_taken': bool(existing_map),
            'statuses': StudentAttendance.STATUS_CHOICES,
        }
        return render(request, self.template_name, context)

    def post(self, request, hall_id):
        hall = get_object_or_404(get_halls_for_user(request.user), pk=hall_id)
        today = date.today()
        students = Student.objects.filter(hall=hall, status='active')
        saved = 0

        for student in students:
            status = request.POST.get(f'status_{student.id}', StudentAttendance.STATUS_ABSENT)
            notes = request.POST.get(f'notes_{student.id}', '')
            arrival_time = request.POST.get(f'arrival_time_{student.id}') or None

            StudentAttendance.objects.update_or_create(
                student=student,
                date=today,
                defaults={
                    'hall': hall,
                    'status': status,
                    'arrival_time': arrival_time,
                    'notes': notes,
                    'recorded_by': request.user,
                }
            )
            saved += 1

        messages.success(request, f'✅ تم تسجيل حضور {saved} طالب بنجاح')
        return redirect('attendance:students')


class StaffAttendanceView(GeneralSupervisorRequiredMixin, View):
    def get(self, request):
        today = date.today()
        selected_raw = request.GET.get('date', str(today))
        selected_date = parse_date(selected_raw, today)

        role = request.GET.get('role', '')
        status = request.GET.get('status', '')
        search = request.GET.get('q', '')

        records = StaffAttendance.objects.filter(
            date=selected_date
        ).select_related('staff', 'recorded_by').order_by('staff__role', 'staff__first_name')

        if role:
            records = records.filter(staff__role=role)
        if status:
            records = records.filter(status=status)
        if search:
            records = records.filter(
                Q(staff__first_name__icontains=search) |
                Q(staff__last_name__icontains=search) |
                Q(staff__username__icontains=search)
            )

        all_today = StaffAttendance.objects.filter(date=selected_date)
        stats = {
            'present': all_today.filter(status=StaffAttendance.STATUS_PRESENT).count(),
            'absent': all_today.filter(status=StaffAttendance.STATUS_ABSENT).count(),
            'late': all_today.filter(status=StaffAttendance.STATUS_LATE).count(),
            'excused': all_today.filter(status=StaffAttendance.STATUS_EXCUSED).count(),
        }

        paginator = Paginator(records, 15)
        page = request.GET.get('page', 1)
        records = paginator.get_page(page)

        context = {
            'records': records,
            'total': paginator.count,
            'stats': stats,
            'selected_date': selected_date,
            'today': today,
            'role_choices': [
                ('teacher', 'معلم'),
                ('hall_supervisor', 'مشرف قاعة'),
            ],
            'status_choices': StaffAttendance.STATUS_CHOICES,
        }
        return render(request, 'attendance/staff_list.html', context)


class StaffAttendanceMarkView(GeneralSupervisorRequiredMixin, View):
    def get(self, request):
        today = date.today()
        target_raw = request.GET.get('date', str(today))
        target_date = parse_date(target_raw, today)

        staff = User.objects.filter(
            is_active=True,
            role__in=['teacher', 'hall_supervisor']
        ).order_by('role', 'first_name', 'last_name')

        existing = StaffAttendance.objects.filter(
            date=target_date
        ).values('staff_id', 'status', 'check_in', 'check_out', 'notes', 'id')

        existing_map = {r['staff_id']: r for r in existing}

        staff_data = []
        for user in staff:
            rec = existing_map.get(user.id, {})
            staff_data.append({
                'user': user,
                'record_id': rec.get('id'),
                'status': rec.get('status', StaffAttendance.STATUS_PRESENT),
                'check_in': rec.get('check_in') or '',
                'check_out': rec.get('check_out') or '',
                'notes': rec.get('notes', ''),
            })

        context = {
            'staff_data': staff_data,
            'target_date': target_date,
            'today': today,
            'status_choices': StaffAttendance.STATUS_CHOICES,
        }
        return render(request, 'attendance/staff_mark.html', context)

    def post(self, request):
        today = date.today()
        target_raw = request.POST.get('date', str(today))
        target_date = parse_date(target_raw, today)
        staff_ids = request.POST.getlist('staff_ids')
        saved = 0

        allowed_staff_ids = set(
            User.objects.filter(
                is_active=True,
                role__in=['teacher', 'hall_supervisor'],
                id__in=staff_ids
            ).values_list('id', flat=True)
        )

        for uid in staff_ids:
            try:
                uid_int = int(uid)
            except (ValueError, TypeError):
                continue

            if uid_int not in allowed_staff_ids:
                continue

            status = request.POST.get(f'status_{uid}', StaffAttendance.STATUS_PRESENT)
            check_in = request.POST.get(f'check_in_{uid}') or None
            check_out = request.POST.get(f'check_out_{uid}') or None
            notes = request.POST.get(f'notes_{uid}', '')

            StaffAttendance.objects.update_or_create(
                staff_id=uid_int,
                date=target_date,
                defaults={
                    'status': status,
                    'check_in': check_in,
                    'check_out': check_out,
                    'notes': notes,
                    'recorded_by': request.user,
                }
            )
            saved += 1

        messages.success(request, f'✅ تم حفظ حضور {saved} موظف ليوم {target_date}')
        return redirect('attendance:staff')


class StaffAttendanceReportView(GeneralSupervisorRequiredMixin, View):
    def get(self, request):
        today = date.today()
        first_day = today.replace(day=1)

        from_date = parse_date(request.GET.get('from'), first_day)
        to_date = parse_date(request.GET.get('to'), today)
        role = request.GET.get('role', '')

        staff = User.objects.filter(
            is_active=True,
            role__in=['teacher', 'hall_supervisor']
        ).order_by('role', 'first_name', 'last_name')

        if role:
            staff = staff.filter(role=role)

        staff_report = []
        for user in staff:
            qs = StaffAttendance.objects.filter(staff=user, date__range=[from_date, to_date])
            present = qs.filter(status=StaffAttendance.STATUS_PRESENT).count()
            late = qs.filter(status=StaffAttendance.STATUS_LATE).count()
            absent = qs.filter(status=StaffAttendance.STATUS_ABSENT).count()
            excused = qs.filter(status=StaffAttendance.STATUS_EXCUSED).count()
            total = qs.count()

            staff_report.append({
                'user': user,
                'present': present,
                'late': late,
                'absent': absent,
                'excused': excused,
                'total': total,
                'percent': round((present + late) / total * 100) if total else 0,
            })

        all_records = StaffAttendance.objects.filter(date__range=[from_date, to_date])
        if role:
            all_records = all_records.filter(staff__role=role)

        context = {
            'staff_report': staff_report,
            'from_date': from_date,
            'to_date': to_date,
            'role_choices': [
                ('teacher', 'معلم'),
                ('hall_supervisor', 'مشرف قاعة'),
            ],
            'total_present': all_records.filter(status=StaffAttendance.STATUS_PRESENT).count(),
            'total_late': all_records.filter(status=StaffAttendance.STATUS_LATE).count(),
            'total_absent': all_records.filter(status=StaffAttendance.STATUS_ABSENT).count(),
            'total_excused': all_records.filter(status=StaffAttendance.STATUS_EXCUSED).count(),
        }
        return render(request, 'attendance/staff_report.html', context)


class AttendanceReportView(GeneralSupervisorRequiredMixin, View):
    def get(self, request):
        today = date.today()
        first_day = today.replace(day=1)

        from_date = parse_date(request.GET.get('from'), first_day)
        to_date = parse_date(request.GET.get('to'), today)
        hall_id = request.GET.get('hall', '')

        allowed_halls = Hall.objects.filter(is_active=True)
        attendances = StudentAttendance.objects.filter(
            date__range=[from_date, to_date]
        ).select_related('student', 'hall', 'recorded_by').order_by('-date', 'hall__name', 'student__first_name')

        if hall_id:
            attendances = attendances.filter(hall_id=hall_id)

        paginator = Paginator(attendances, 20)
        page = request.GET.get('page', 1)
        attendances = paginator.get_page(page)

        base_qs = StudentAttendance.objects.filter(date__range=[from_date, to_date])
        if hall_id:
            base_qs = base_qs.filter(hall_id=hall_id)

        context = {
            'attendances': attendances,
            'halls': allowed_halls,
            'from_date': from_date,
            'to_date': to_date,
            'selected_hall': hall_id,
            'total': paginator.count,
            'present': base_qs.filter(status=StudentAttendance.STATUS_PRESENT).count(),
            'absent': base_qs.filter(status=StudentAttendance.STATUS_ABSENT).count(),
            'late': base_qs.filter(status=StudentAttendance.STATUS_LATE).count(),
            'excused': base_qs.filter(status=StudentAttendance.STATUS_EXCUSED).count(),
        }
        return render(request, 'attendance/report.html', context)