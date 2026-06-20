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


# ══════════════════════════════════════════
#  دوال مساعدة عامة
# ══════════════════════════════════════════

def parse_date(value, default):
    """
    تحويل النص القادم من GET/POST إلى تاريخ.
    لو التاريخ غير صالح يرجع القيمة الافتراضية.
    """
    try:
        return datetime.strptime(value, '%Y-%m-%d').date() if value else default
    except (ValueError, TypeError):
        return default


def get_halls_for_user(user):
    """
    القاعات المسموح للمستخدم التعامل معها في الحضور والانصراف.

    المدير العام:
        يرى كل القاعات النشطة.

    المشرف العام:
        يرى القاعات المسندة له من جدول GeneralSupervisorHallAssignment.
        مع fallback للنظام القديم Hall.general_supervisor.

    مشرف القاعة:
        يرى القاعات التي هو مشرفها.

    غير ذلك:
        لا يرى قاعات.
    """
    if not user.is_authenticated:
        return Hall.objects.none()

    base_qs = Hall.objects.filter(is_active=True).select_related(
        'teacher',
        'supervisor',
        'age_group',
    ).prefetch_related(
        'general_supervisor_assignments__supervisor'
    )

    if user.is_general_manager:
        return base_qs

    if user.is_general_supervisor:
        return base_qs.filter(
            Q(general_supervisor_assignments__supervisor=user) |
            Q(general_supervisor=user)
        ).distinct()

    if user.is_hall_supervisor:
        return base_qs.filter(supervisor=user)

    return Hall.objects.none()


def get_allowed_student_attendance_queryset(user, from_date=None, to_date=None):
    """
    QuerySet موحد لتقارير حضور الطلاب حسب صلاحية المستخدم.
    """
    allowed_halls = get_halls_for_user(user)

    qs = StudentAttendance.objects.filter(
        hall__in=allowed_halls
    ).select_related(
        'student',
        'hall',
        'recorded_by'
    ).order_by(
        '-date',
        'hall__name',
        'student__first_name',
        'student__last_name'
    )

    if from_date and to_date:
        qs = qs.filter(date__range=[from_date, to_date])

    return qs


# ══════════════════════════════════════════
#  اختيار القاعة لتسجيل حضور الطلاب
# ══════════════════════════════════════════

class StudentAttendanceView(HallSupervisorRequiredMixin, View):
    def get(self, request):
        context = {
            'halls': get_halls_for_user(request.user),
            'today': date.today(),
        }

        return render(request, 'attendance/select_hall.html', context)


# ══════════════════════════════════════════
#  تسجيل حضور وانصراف الطلاب
# ══════════════════════════════════════════
def get_first_post_value(post_data, key, default=None):
    """
    تستخدم عند وجود أكثر من input بنفس الاسم في الصفحة
    مثل نسخة الديسكتوب ونسخة الموبايل.

    ترجع أول قيمة غير فارغة بدل request.POST.get
    حتى لا تضيع قيمة وقت الحضور أو الانصراف.
    """
    values = post_data.getlist(key)

    for value in values:
        if value not in [None, '']:
            return value

    return default

class TakeAttendanceView(HallSupervisorRequiredMixin, View):
    template_name = 'attendance/take_attendance.html'

    def get(self, request, hall_id):
        hall = get_object_or_404(
            get_halls_for_user(request.user),
            pk=hall_id
        )

        today = date.today()

        students = Student.objects.filter(
            hall=hall,
            status='active'
        ).select_related(
            'parent',
            'age_group'
        ).order_by(
            'first_name',
            'last_name'
        )

        existing = StudentAttendance.objects.filter(
            hall=hall,
            date=today
        ).values(
            'student_id',
            'status',
            'notes',
            'arrival_time',
            'departure_time',
        )

        existing_map = {
            row['student_id']: row
            for row in existing
        }

        students_data = []

        for student in students:
            rec = existing_map.get(student.id, {})

            students_data.append({
                'student': student,
                'status': rec.get('status', StudentAttendance.STATUS_PRESENT),
                'notes': rec.get('notes') or '',
                'arrival_time': rec.get('arrival_time') or '',
                'departure_time': rec.get('departure_time') or '',
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
        hall = get_object_or_404(
            get_halls_for_user(request.user),
            pk=hall_id
        )

        today = date.today()

        students = Student.objects.filter(
            hall=hall,
            status='active'
        ).order_by(
            'first_name',
            'last_name'
        )

        saved = 0

        for student in students:
            status = get_first_post_value(
                request.POST,
                f'status_{student.id}',
                StudentAttendance.STATUS_ABSENT
            )

            arrival_time = get_first_post_value(
                request.POST,
                f'arrival_time_{student.id}',
                None
            )

            departure_time = get_first_post_value(
                request.POST,
                f'departure_time_{student.id}',
                None
            )

            notes = get_first_post_value(
                request.POST,
                f'notes_{student.id}',
                ''
            )

            StudentAttendance.objects.update_or_create(
                student=student,
                date=today,
                defaults={
                    'hall': hall,
                    'status': status,
                    'arrival_time': arrival_time,
                    'departure_time': departure_time,
                    'notes': notes or '',
                    'recorded_by': request.user,
                }
            )

            saved += 1

        messages.success(
            request,
            f'✅ تم حفظ حضور وانصراف {saved} طالب بنجاح'
        )

        return redirect('attendance:students')
    
# ══════════════════════════════════════════
#  قائمة حضور الموظفين
# ══════════════════════════════════════════

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
        ).select_related(
            'staff',
            'recorded_by'
        ).order_by(
            'staff__role',
            'staff__first_name',
            'staff__last_name'
        )

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


# ══════════════════════════════════════════
#  تسجيل حضور الموظفين
# ══════════════════════════════════════════

class StaffAttendanceMarkView(GeneralSupervisorRequiredMixin, View):
    def get(self, request):
        today = date.today()
        target_raw = request.GET.get('date', str(today))
        target_date = parse_date(target_raw, today)

        staff = User.objects.filter(
            is_active=True,
            role__in=['teacher', 'hall_supervisor']
        ).order_by(
            'role',
            'first_name',
            'last_name'
        )

        existing = StaffAttendance.objects.filter(
            date=target_date
        ).values(
            'staff_id',
            'status',
            'check_in',
            'check_out',
            'notes',
            'id'
        )

        existing_map = {
            row['staff_id']: row
            for row in existing
        }

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

            status = request.POST.get(
                f'status_{uid}',
                StaffAttendance.STATUS_PRESENT
            )

            check_in = request.POST.get(
                f'check_in_{uid}'
            ) or None

            check_out = request.POST.get(
                f'check_out_{uid}'
            ) or None

            notes = request.POST.get(
                f'notes_{uid}',
                ''
            )

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

        messages.success(
            request,
            f'✅ تم حفظ حضور {saved} موظف ليوم {target_date}'
        )

        return redirect('attendance:staff')


# ══════════════════════════════════════════
#  تقرير حضور الموظفين
# ══════════════════════════════════════════

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
        ).order_by(
            'role',
            'first_name',
            'last_name'
        )

        if role:
            staff = staff.filter(role=role)

        staff_report = []

        for user in staff:
            qs = StaffAttendance.objects.filter(
                staff=user,
                date__range=[from_date, to_date]
            )

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

        all_records = StaffAttendance.objects.filter(
            date__range=[from_date, to_date]
        )

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


# ══════════════════════════════════════════
#  تقرير حضور الطلاب
# ══════════════════════════════════════════

# class AttendanceReportView(GeneralSupervisorRequiredMixin, View):
#     def get(self, request):
#         today = date.today()
#         first_day = today.replace(day=1)

#         from_date = parse_date(request.GET.get('from'), first_day)
#         to_date = parse_date(request.GET.get('to'), today)
#         hall_id = request.GET.get('hall', '')

#         allowed_halls = get_halls_for_user(request.user)

#         attendances = StudentAttendance.objects.filter(
#             hall__in=allowed_halls,
#             date__range=[from_date, to_date]
#         ).select_related(
#             'student',
#             'hall',
#             'recorded_by'
#         ).order_by(
#             '-date',
#             'hall__name',
#             'student__first_name',
#             'student__last_name'
#         )

#         if hall_id:
#             attendances = attendances.filter(hall_id=hall_id)

#         paginator = Paginator(attendances, 20)
#         page = request.GET.get('page', 1)
#         attendances_page = paginator.get_page(page)

#         base_qs = StudentAttendance.objects.filter(
#             hall__in=allowed_halls,
#             date__range=[from_date, to_date]
#         )

#         if hall_id:
#             base_qs = base_qs.filter(hall_id=hall_id)

#         context = {
#             'attendances': attendances_page,
#             'halls': allowed_halls,
#             'from_date': from_date,
#             'to_date': to_date,
#             'selected_hall': hall_id,
#             'total': paginator.count,
#             'present': base_qs.filter(status=StudentAttendance.STATUS_PRESENT).count(),
#             'absent': base_qs.filter(status=StudentAttendance.STATUS_ABSENT).count(),
#             'late': base_qs.filter(status=StudentAttendance.STATUS_LATE).count(),
#             'excused': base_qs.filter(status=StudentAttendance.STATUS_EXCUSED).count(),
#         }

#         return render(request, 'attendance/report.html', context)

class AttendanceReportView(HallSupervisorRequiredMixin, View):
    def get(self, request):
        today = date.today()
        first_day = today.replace(day=1)

        from_date = parse_date(request.GET.get('from'), first_day)
        to_date = parse_date(request.GET.get('to'), today)
        hall_id = request.GET.get('hall', '')

        if from_date > to_date:
            from_date, to_date = to_date, from_date

        allowed_halls = get_halls_for_user(request.user)

        attendances = StudentAttendance.objects.filter(
            hall__in=allowed_halls,
            date__range=[from_date, to_date]
        ).select_related(
            'student',
            'hall',
            'recorded_by',
            'student__parent',
        ).order_by(
            '-date',
            'hall__name',
            'student__first_name',
            'student__last_name'
        )

        if hall_id:
            attendances = attendances.filter(hall_id=hall_id)

        paginator = Paginator(attendances, 20)
        page = request.GET.get('page', 1)
        attendances_page = paginator.get_page(page)

        base_qs = StudentAttendance.objects.filter(
            hall__in=allowed_halls,
            date__range=[from_date, to_date]
        )

        if hall_id:
            base_qs = base_qs.filter(hall_id=hall_id)

        context = {
            'attendances': attendances_page,
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

from django.db.models import Count, Q, F, FloatField, ExpressionWrapper, Value
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator
from datetime import date

class StudentAttendanceSummaryView(HallSupervisorRequiredMixin, View):
    template_name = 'attendance/student_summary.html'

    def get(self, request):
        today = date.today()
        first_day = today.replace(day=1)

        from_date = parse_date(request.GET.get('from'), first_day)
        to_date = parse_date(request.GET.get('to'), today)
        hall_id = request.GET.get('hall', '')
        search = request.GET.get('q', '').strip()

        if from_date > to_date:
            from_date, to_date = to_date, from_date

        allowed_halls = get_halls_for_user(request.user)

        qs = StudentAttendance.objects.filter(
            hall__in=allowed_halls,
            date__range=[from_date, to_date]
        )

        if hall_id:
            qs = qs.filter(hall_id=hall_id)

        if search:
            qs = qs.filter(
                Q(student__first_name__icontains=search) |
                Q(student__last_name__icontains=search)
            )

        summary = qs.values(
            'student_id',
            'student__first_name',
            'student__last_name',
            'student__parent__first_name',
            'student__parent__last_name',
            'student__parent__username',
            'hall__name',
        ).annotate(
            present_count=Count('id', filter=Q(status=StudentAttendance.STATUS_PRESENT)),
            absent_count=Count('id', filter=Q(status=StudentAttendance.STATUS_ABSENT)),
            late_count=Count('id', filter=Q(status=StudentAttendance.STATUS_LATE)),
            excused_count=Count('id', filter=Q(status=StudentAttendance.STATUS_EXCUSED)),
            total_days=Count('id'),
        ).order_by(
            '-present_count',
            'student__first_name',
            'student__last_name'
        )

        summary_list = []
        for row in summary:
            total_days = row['total_days'] or 0
            present_count = row['present_count'] or 0
            attendance_rate = round((present_count / total_days) * 100, 1) if total_days else 0

            row['attendance_rate'] = attendance_rate
            summary_list.append(row)

        paginator = Paginator(summary_list, 20)
        page = request.GET.get('page', 1)
        summary_page = paginator.get_page(page)

        totals = qs.aggregate(
            total_present=Count('id', filter=Q(status=StudentAttendance.STATUS_PRESENT)),
            total_absent=Count('id', filter=Q(status=StudentAttendance.STATUS_ABSENT)),
            total_late=Count('id', filter=Q(status=StudentAttendance.STATUS_LATE)),
            total_excused=Count('id', filter=Q(status=StudentAttendance.STATUS_EXCUSED)),
            total_records=Count('id'),
            total_students=Count('student', distinct=True),
        )

        context = {
            'summary': summary_page,
            'from_date': from_date,
            'to_date': to_date,
            'halls': allowed_halls,
            'selected_hall': hall_id,
            'search': search,
            'total_students': totals['total_students'] or 0,
            'total_records': totals['total_records'] or 0,
            'total_present': totals['total_present'] or 0,
            'total_absent': totals['total_absent'] or 0,
            'total_late': totals['total_late'] or 0,
            'total_excused': totals['total_excused'] or 0,
        }

        return render(request, self.template_name, context)


class DailyAttendanceListView(HallSupervisorRequiredMixin, View):
    template_name = 'attendance/daily_attendance_list.html'

    def get(self, request):
        today = date.today()
        selected_date = parse_date(request.GET.get('date'), today)
        hall_id = request.GET.get('hall', '')
        status = request.GET.get('status', '')
        search = request.GET.get('q', '')

        allowed_halls = get_halls_for_user(request.user)

        student_records = StudentAttendance.objects.filter(
            hall__in=allowed_halls,
            date=selected_date
        ).select_related(
            'student',
            'hall',
            'recorded_by'
        ).order_by(
            'hall__name',
            'student__first_name',
            'student__last_name'
        )

        if hall_id:
            student_records = student_records.filter(hall_id=hall_id)

        if status:
            student_records = student_records.filter(status=status)

        if search:
            student_records = student_records.filter(
                Q(student__first_name__icontains=search) |
                Q(student__last_name__icontains=search)
            )

        staff_records = StaffAttendance.objects.filter(
            date=selected_date
        ).select_related(
            'staff',
            'recorded_by'
        ).order_by(
            'staff__role',
            'staff__first_name',
            'staff__last_name'
        )

        if status:
            staff_records = staff_records.filter(status=status)

        if search:
            staff_records = staff_records.filter(
                Q(staff__first_name__icontains=search) |
                Q(staff__last_name__icontains=search) |
                Q(staff__username__icontains=search)
            )

        student_stats = {
            'present': student_records.filter(status=StudentAttendance.STATUS_PRESENT).count(),
            'absent': student_records.filter(status=StudentAttendance.STATUS_ABSENT).count(),
            'late': student_records.filter(status=StudentAttendance.STATUS_LATE).count(),
            'excused': student_records.filter(status=StudentAttendance.STATUS_EXCUSED).count(),
        }

        staff_stats = {
            'present': staff_records.filter(status=StaffAttendance.STATUS_PRESENT).count(),
            'absent': staff_records.filter(status=StaffAttendance.STATUS_ABSENT).count(),
            'late': staff_records.filter(status=StaffAttendance.STATUS_LATE).count(),
            'excused': staff_records.filter(status=StaffAttendance.STATUS_EXCUSED).count(),
        }

        context = {
            'selected_date': selected_date,
            'today': today,
            'halls': allowed_halls,
            'selected_hall': hall_id,
            'selected_status': status,
            'search': search,
            'student_records': student_records,
            'staff_records': staff_records,
            'student_stats': student_stats,
            'staff_stats': staff_stats,
            'status_choices': StudentAttendance.STATUS_CHOICES,
        }

        return render(request, self.template_name, context)
    
# from datetime import date, datetime

# from django.contrib import messages
# from django.core.paginator import Paginator
# from django.db.models import Q
# from django.shortcuts import get_object_or_404, redirect, render
# from django.views import View

# from accounts.models import User
# from accounts.permissions import HallSupervisorRequiredMixin, GeneralSupervisorRequiredMixin
# from halls.models import Hall
# from students.models import Student
# from .models import StudentAttendance, StaffAttendance


# def parse_date(value, default):
#     try:
#         return datetime.strptime(value, '%Y-%m-%d').date() if value else default
#     except (ValueError, TypeError):
#         return default


# def get_halls_for_user(user):
#     if user.is_general_manager:
#         return Hall.objects.filter(is_active=True)
#     if user.is_general_supervisor:
#         return Hall.objects.filter(is_active=True, general_supervisor=user)
#     if user.is_hall_supervisor:
#         return Hall.objects.filter(is_active=True, supervisor=user)
#     return Hall.objects.none()


# class StudentAttendanceView(HallSupervisorRequiredMixin, View):
#     def get(self, request):
#         context = {
#             'halls': get_halls_for_user(request.user),
#             'today': date.today(),
#         }
#         return render(request, 'attendance/select_hall.html', context)


# class TakeAttendanceView(HallSupervisorRequiredMixin, View):
#     template_name = 'attendance/take_attendance.html'

#     def get(self, request, hall_id):
#         hall = get_object_or_404(get_halls_for_user(request.user), pk=hall_id)
#         today = date.today()
#         students = Student.objects.filter(hall=hall, status='active').select_related('parent', 'age_group')

#         existing = StudentAttendance.objects.filter(
#             hall=hall,
#             date=today
#         ).values('student_id', 'status', 'notes', 'arrival_time')

#         existing_map = {r['student_id']: r for r in existing}

#         students_data = []
#         for student in students:
#             rec = existing_map.get(student.id, {})
#             students_data.append({
#                 'student': student,
#                 'status': rec.get('status', StudentAttendance.STATUS_PRESENT),
#                 'notes': rec.get('notes', ''),
#                 'arrival_time': rec.get('arrival_time', ''),
#             })

#         context = {
#             'hall': hall,
#             'today': today,
#             'students_data': students_data,
#             'already_taken': bool(existing_map),
#             'statuses': StudentAttendance.STATUS_CHOICES,
#         }
#         return render(request, self.template_name, context)

#     def post(self, request, hall_id):
#         hall = get_object_or_404(get_halls_for_user(request.user), pk=hall_id)
#         today = date.today()
#         students = Student.objects.filter(hall=hall, status='active')
#         saved = 0

#         for student in students:
#             status = request.POST.get(f'status_{student.id}', StudentAttendance.STATUS_ABSENT)
#             notes = request.POST.get(f'notes_{student.id}', '')
#             arrival_time = request.POST.get(f'arrival_time_{student.id}') or None

#             StudentAttendance.objects.update_or_create(
#                 student=student,
#                 date=today,
#                 defaults={
#                     'hall': hall,
#                     'status': status,
#                     'arrival_time': arrival_time,
#                     'notes': notes,
#                     'recorded_by': request.user,
#                 }
#             )
#             saved += 1

#         messages.success(request, f'✅ تم تسجيل حضور {saved} طالب بنجاح')
#         return redirect('attendance:students')


# class StaffAttendanceView(GeneralSupervisorRequiredMixin, View):
#     def get(self, request):
#         today = date.today()
#         selected_raw = request.GET.get('date', str(today))
#         selected_date = parse_date(selected_raw, today)

#         role = request.GET.get('role', '')
#         status = request.GET.get('status', '')
#         search = request.GET.get('q', '')

#         records = StaffAttendance.objects.filter(
#             date=selected_date
#         ).select_related('staff', 'recorded_by').order_by('staff__role', 'staff__first_name')

#         if role:
#             records = records.filter(staff__role=role)
#         if status:
#             records = records.filter(status=status)
#         if search:
#             records = records.filter(
#                 Q(staff__first_name__icontains=search) |
#                 Q(staff__last_name__icontains=search) |
#                 Q(staff__username__icontains=search)
#             )

#         all_today = StaffAttendance.objects.filter(date=selected_date)
#         stats = {
#             'present': all_today.filter(status=StaffAttendance.STATUS_PRESENT).count(),
#             'absent': all_today.filter(status=StaffAttendance.STATUS_ABSENT).count(),
#             'late': all_today.filter(status=StaffAttendance.STATUS_LATE).count(),
#             'excused': all_today.filter(status=StaffAttendance.STATUS_EXCUSED).count(),
#         }

#         paginator = Paginator(records, 15)
#         page = request.GET.get('page', 1)
#         records = paginator.get_page(page)

#         context = {
#             'records': records,
#             'total': paginator.count,
#             'stats': stats,
#             'selected_date': selected_date,
#             'today': today,
#             'role_choices': [
#                 ('teacher', 'معلم'),
#                 ('hall_supervisor', 'مشرف قاعة'),
#             ],
#             'status_choices': StaffAttendance.STATUS_CHOICES,
#         }
#         return render(request, 'attendance/staff_list.html', context)


# class StaffAttendanceMarkView(GeneralSupervisorRequiredMixin, View):
#     def get(self, request):
#         today = date.today()
#         target_raw = request.GET.get('date', str(today))
#         target_date = parse_date(target_raw, today)

#         staff = User.objects.filter(
#             is_active=True,
#             role__in=['teacher', 'hall_supervisor']
#         ).order_by('role', 'first_name', 'last_name')

#         existing = StaffAttendance.objects.filter(
#             date=target_date
#         ).values('staff_id', 'status', 'check_in', 'check_out', 'notes', 'id')

#         existing_map = {r['staff_id']: r for r in existing}

#         staff_data = []
#         for user in staff:
#             rec = existing_map.get(user.id, {})
#             staff_data.append({
#                 'user': user,
#                 'record_id': rec.get('id'),
#                 'status': rec.get('status', StaffAttendance.STATUS_PRESENT),
#                 'check_in': rec.get('check_in') or '',
#                 'check_out': rec.get('check_out') or '',
#                 'notes': rec.get('notes', ''),
#             })

#         context = {
#             'staff_data': staff_data,
#             'target_date': target_date,
#             'today': today,
#             'status_choices': StaffAttendance.STATUS_CHOICES,
#         }
#         return render(request, 'attendance/staff_mark.html', context)

#     def post(self, request):
#         today = date.today()
#         target_raw = request.POST.get('date', str(today))
#         target_date = parse_date(target_raw, today)
#         staff_ids = request.POST.getlist('staff_ids')
#         saved = 0

#         allowed_staff_ids = set(
#             User.objects.filter(
#                 is_active=True,
#                 role__in=['teacher', 'hall_supervisor'],
#                 id__in=staff_ids
#             ).values_list('id', flat=True)
#         )

#         for uid in staff_ids:
#             try:
#                 uid_int = int(uid)
#             except (ValueError, TypeError):
#                 continue

#             if uid_int not in allowed_staff_ids:
#                 continue

#             status = request.POST.get(f'status_{uid}', StaffAttendance.STATUS_PRESENT)
#             check_in = request.POST.get(f'check_in_{uid}') or None
#             check_out = request.POST.get(f'check_out_{uid}') or None
#             notes = request.POST.get(f'notes_{uid}', '')

#             StaffAttendance.objects.update_or_create(
#                 staff_id=uid_int,
#                 date=target_date,
#                 defaults={
#                     'status': status,
#                     'check_in': check_in,
#                     'check_out': check_out,
#                     'notes': notes,
#                     'recorded_by': request.user,
#                 }
#             )
#             saved += 1

#         messages.success(request, f'✅ تم حفظ حضور {saved} موظف ليوم {target_date}')
#         return redirect('attendance:staff')


# class StaffAttendanceReportView(GeneralSupervisorRequiredMixin, View):
#     def get(self, request):
#         today = date.today()
#         first_day = today.replace(day=1)

#         from_date = parse_date(request.GET.get('from'), first_day)
#         to_date = parse_date(request.GET.get('to'), today)
#         role = request.GET.get('role', '')

#         staff = User.objects.filter(
#             is_active=True,
#             role__in=['teacher', 'hall_supervisor']
#         ).order_by('role', 'first_name', 'last_name')

#         if role:
#             staff = staff.filter(role=role)

#         staff_report = []
#         for user in staff:
#             qs = StaffAttendance.objects.filter(staff=user, date__range=[from_date, to_date])
#             present = qs.filter(status=StaffAttendance.STATUS_PRESENT).count()
#             late = qs.filter(status=StaffAttendance.STATUS_LATE).count()
#             absent = qs.filter(status=StaffAttendance.STATUS_ABSENT).count()
#             excused = qs.filter(status=StaffAttendance.STATUS_EXCUSED).count()
#             total = qs.count()

#             staff_report.append({
#                 'user': user,
#                 'present': present,
#                 'late': late,
#                 'absent': absent,
#                 'excused': excused,
#                 'total': total,
#                 'percent': round((present + late) / total * 100) if total else 0,
#             })

#         all_records = StaffAttendance.objects.filter(date__range=[from_date, to_date])
#         if role:
#             all_records = all_records.filter(staff__role=role)

#         context = {
#             'staff_report': staff_report,
#             'from_date': from_date,
#             'to_date': to_date,
#             'role_choices': [
#                 ('teacher', 'معلم'),
#                 ('hall_supervisor', 'مشرف قاعة'),
#             ],
#             'total_present': all_records.filter(status=StaffAttendance.STATUS_PRESENT).count(),
#             'total_late': all_records.filter(status=StaffAttendance.STATUS_LATE).count(),
#             'total_absent': all_records.filter(status=StaffAttendance.STATUS_ABSENT).count(),
#             'total_excused': all_records.filter(status=StaffAttendance.STATUS_EXCUSED).count(),
#         }
#         return render(request, 'attendance/staff_report.html', context)


# class AttendanceReportView(GeneralSupervisorRequiredMixin, View):
#     def get(self, request):
#         today = date.today()
#         first_day = today.replace(day=1)

#         from_date = parse_date(request.GET.get('from'), first_day)
#         to_date = parse_date(request.GET.get('to'), today)
#         hall_id = request.GET.get('hall', '')

#         allowed_halls = Hall.objects.filter(is_active=True)
#         attendances = StudentAttendance.objects.filter(
#             date__range=[from_date, to_date]
#         ).select_related('student', 'hall', 'recorded_by').order_by('-date', 'hall__name', 'student__first_name')

#         if hall_id:
#             attendances = attendances.filter(hall_id=hall_id)

#         paginator = Paginator(attendances, 20)
#         page = request.GET.get('page', 1)
#         attendances = paginator.get_page(page)

#         base_qs = StudentAttendance.objects.filter(date__range=[from_date, to_date])
#         if hall_id:
#             base_qs = base_qs.filter(hall_id=hall_id)

#         context = {
#             'attendances': attendances,
#             'halls': allowed_halls,
#             'from_date': from_date,
#             'to_date': to_date,
#             'selected_hall': hall_id,
#             'total': paginator.count,
#             'present': base_qs.filter(status=StudentAttendance.STATUS_PRESENT).count(),
#             'absent': base_qs.filter(status=StudentAttendance.STATUS_ABSENT).count(),
#             'late': base_qs.filter(status=StudentAttendance.STATUS_LATE).count(),
#             'excused': base_qs.filter(status=StudentAttendance.STATUS_EXCUSED).count(),
#         }
#         return render(request, 'attendance/report.html', context)