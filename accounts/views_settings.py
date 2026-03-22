from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from django.db.models import Count
from datetime import date

from accounts.permissions import GeneralManagerRequiredMixin
from accounts.models import User, SiteSettings
from students.models import Student, AgeGroup
from halls.models import Hall


# ============================================================
# لوحة الإعدادات الرئيسية
# ============================================================
class SettingsHomeView(GeneralManagerRequiredMixin, View):
    def get(self, request):
        settings = SiteSettings.get_settings()
        context  = {
            'settings':        settings,
            'total_users':     User.objects.count(),
            'total_students':  Student.objects.count(),
            'total_halls':     Hall.objects.count(),
            'total_age_groups': AgeGroup.objects.count(),
            'staff_by_role':   User.objects.values('role').annotate(count=Count('id')),
        }
        return render(request, 'settings/home.html', context)


# ============================================================
# إعدادات المقرأة
# ============================================================
class SiteSettingsView(GeneralManagerRequiredMixin, View):
    template_name = 'settings/site.html'

    def get(self, request):
        from .forms_settings import SiteSettingsForm
        settings = SiteSettings.get_settings()
        form     = SiteSettingsForm(instance=settings)
        return render(request, self.template_name, {'form': form, 'settings': settings})

    def post(self, request):
        from .forms_settings import SiteSettingsForm
        settings = SiteSettings.get_settings()
        form     = SiteSettingsForm(request.POST, request.FILES, instance=settings)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.updated_by = request.user
            obj.save()
            messages.success(request, '✅ تم حفظ إعدادات المقرأة بنجاح')
            return redirect('settings:home')
        return render(request, self.template_name, {'form': form, 'settings': settings})


# ============================================================
# إدارة المستخدمين
# ============================================================
from django.core.paginator import Paginator  # ← أضفها فوق

class UsersManageView(GeneralManagerRequiredMixin, View):
    def get(self, request):
        role   = request.GET.get('role', '')
        search = request.GET.get('q', '')
        users  = User.objects.all().order_by('role', 'first_name')

        if role:
            users = users.filter(role=role)
        if search:
            users = users.filter(
                first_name__icontains=search
            ) | users.filter(
                last_name__icontains=search
            ) | users.filter(
                username__icontains=search
            )

        # Pagination ✅
        paginator = Paginator(users, 10)
        page      = request.GET.get('page', 1)
        users     = paginator.get_page(page)

        context = {
            'users':        users,
            'total':        paginator.count,
            'role_choices': User.ROLES,
            'roles_count':  User.objects.values('role').annotate(count=Count('id')),
        }
        return render(request, 'settings/users/list.html', context)


class UserCreateView(GeneralManagerRequiredMixin, View):
    template_name = 'settings/users/form.html'

    def get(self, request):
        from .forms_settings import UserCreateForm
        return render(request, self.template_name, {
            'form': UserCreateForm(), 'action': 'إضافة'
        })

    def post(self, request):
        from .forms_settings import UserCreateForm
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, f'✅ تم إنشاء حساب {user.get_full_name()} بنجاح')
            return redirect('settings:users')
        return render(request, self.template_name, {'form': form, 'action': 'إضافة'})


class UserUpdateView(GeneralManagerRequiredMixin, View):
    template_name = 'settings/users/form.html'

    def get(self, request, pk):
        from .forms_settings import UserUpdateForm
        user = get_object_or_404(User, pk=pk)
        form = UserUpdateForm(instance=user)
        return render(request, self.template_name, {
            'form': form, 'action': 'تعديل', 'target_user': user
        })

    def post(self, request, pk):
        from .forms_settings import UserUpdateForm
        user = get_object_or_404(User, pk=pk)
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ تم تعديل بيانات {user.get_full_name()}')
            return redirect('settings:users')
        return render(request, self.template_name, {
            'form': form, 'action': 'تعديل', 'target_user': user
        })


class UserToggleActiveView(GeneralManagerRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user == request.user:
            messages.error(request, '❌ لا يمكنك تعطيل حسابك الخاص')
            return redirect('settings:users')
        user.is_active = not user.is_active
        user.save()
        status = 'تفعيل' if user.is_active else 'تعطيل'
        messages.success(request, f'✅ تم {status} حساب {user.get_full_name()}')
        return redirect('settings:users')


class UserResetPasswordView(GeneralManagerRequiredMixin, View):
    def post(self, request, pk):
        user         = get_object_or_404(User, pk=pk)
        new_password = request.POST.get('new_password', 'Pass@1234')
        user.set_password(new_password)
        user.save()
        messages.success(
            request,
            f'✅ تم إعادة تعيين كلمة مرور {user.get_full_name()} — الكلمة الجديدة: {new_password}'
        )
        return redirect('settings:users')


# ============================================================
# إدارة الفئات العمرية
# ============================================================
class AgeGroupsView(GeneralManagerRequiredMixin, View):
    def get(self, request):
        from students.models import AgeGroup
        age_groups = AgeGroup.objects.annotate(
            students_count=Count('students'),
            halls_count=Count('halls')
        )
        context = {
            'age_groups': age_groups,
            'total':      age_groups.count(),
        }
        return render(request, 'settings/age_groups.html', context)


class AgeGroupCreateView(GeneralManagerRequiredMixin, View):
    template_name = 'settings/age_group_form.html'

    def get(self, request):
        from .forms_settings import AgeGroupForm
        return render(request, self.template_name, {
            'form': AgeGroupForm(), 'action': 'إضافة'
        })

    def post(self, request):
        from .forms_settings import AgeGroupForm
        form = AgeGroupForm(request.POST)
        if form.is_valid():
            ag = form.save()
            messages.success(request, f'✅ تم إضافة فئة {ag.name}')
            return redirect('settings:age_groups')
        return render(request, self.template_name, {'form': form, 'action': 'إضافة'})


class AgeGroupUpdateView(GeneralManagerRequiredMixin, View):
    template_name = 'settings/age_group_form.html'

    def get(self, request, pk):
        from .forms_settings import AgeGroupForm
        from students.models import AgeGroup
        ag   = get_object_or_404(AgeGroup, pk=pk)
        form = AgeGroupForm(instance=ag)
        return render(request, self.template_name, {
            'form': form, 'action': 'تعديل', 'age_group': ag
        })

    def post(self, request, pk):
        from .forms_settings import AgeGroupForm
        from students.models import AgeGroup
        ag   = get_object_or_404(AgeGroup, pk=pk)
        form = AgeGroupForm(request.POST, instance=ag)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ تم تعديل فئة {ag.name}')
            return redirect('settings:age_groups')
        return render(request, self.template_name, {
            'form': form, 'action': 'تعديل', 'age_group': ag
        })


class AgeGroupDeleteView(GeneralManagerRequiredMixin, View):
    def post(self, request, pk):
        from students.models import AgeGroup
        ag = get_object_or_404(AgeGroup, pk=pk)
        if ag.students.exists():
            messages.error(request, f'❌ لا يمكن حذف "{ag.name}" — يوجد طلاب مرتبطون بها')
        elif ag.halls.exists():
            messages.error(request, f'❌ لا يمكن حذف "{ag.name}" — يوجد قاعات مرتبطة بها')
        else:
            ag.delete()
            messages.success(request, f'✅ تم حذف الفئة')
        return redirect('settings:age_groups')
