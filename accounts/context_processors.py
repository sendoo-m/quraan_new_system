from django.conf import settings


def site_settings(request):
    """بيانات ثابتة تظهر في كل القوالب"""
    return {
        'SITE_NAME': 'مقرأة تحفيظ القرآن الكريم',
        'SITE_NAME_EN': 'Quran Memorization School',
        'SITE_VERSION': '1.0.0',
    }

def user_role_context(request):
    if not request.user.is_authenticated:
        return {}
    user = request.user
    return {
        'is_general_manager':    user.is_general_manager,
        'is_general_supervisor': user.is_general_supervisor,
        'is_hall_supervisor':    user.is_hall_supervisor,
        'is_teacher':            user.is_teacher,
        'is_parent':             user.is_parent,
        'user_role_display':     user.get_role_display(),
    }
# def user_role_context(request):
#     """بيانات المستخدم والدور الوظيفي لكل القوالب"""
#     if not request.user.is_authenticated:
#         return {}

#     return {
#         'is_general_manager':    request.user.is_general_manager,
#         'is_general_supervisor': request.user.is_general_supervisor,
#         'is_hall_supervisor':    request.user.is_hall_supervisor,
#         'is_teacher':            request.user.is_teacher,
#         'is_parent':             request.user.is_parent,
#         'user_role_display':     request.user.get_role_display(),
#         'is_staff_member':       request.user.role != 'parent',
#     }

from .models import SiteSettings

def site_settings(request):
    settings = SiteSettings.get_settings()
    return {
        'SITE_NAME':        settings.name,
        'SITE_LOGO':        settings.logo,
        'SITE_PHONE':       settings.phone,
        'SITE_SETTINGS':    settings,
        'ALLOW_REGISTRATION': settings.allow_registration,
    }
