"""Users admin."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.users.models import User


class UserAdmin(BaseUserAdmin):
    """Add the UserSetting to the User admin interface."""

    model = User


admin.site.register(User, UserAdmin)
