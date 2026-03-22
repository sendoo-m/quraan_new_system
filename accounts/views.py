from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views import View
from django.utils.decorators import method_decorator
from .models import User


class LoginView(View):
    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user     = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            messages.success(request, f'مرحباً {user.get_full_name()} 👋')
            return redirect('dashboard')

        messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة')
        return render(request, self.template_name)


class LogoutView(View):
    def post(self, request):
        logout(request)
        return redirect('accounts:login')


@method_decorator(login_required, name='dispatch')
class DashboardView(View):
    def get(self, request):
        user = request.user
        context = {}

        if user.is_general_manager:
            return redirect('dashboard:manager')
        elif user.is_general_supervisor:
            return redirect('dashboard:supervisor')
        elif user.is_hall_supervisor:
            return redirect('dashboard:hall_supervisor')
        elif user.is_teacher:
            return redirect('dashboard:teacher')
        elif user.is_parent:
            return redirect('dashboard:parent')

        return render(request, 'accounts/dashboard_base.html', context)
