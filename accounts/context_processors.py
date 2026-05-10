from django.conf import settings


def site_settings(request):
    """بيانات ثابتة تظهر في كل القوالب"""
    return {
        'SITE_NAME': 'كُتَّاب المنار الصيفي',
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

