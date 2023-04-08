from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserChangeForm, CustomUserCreationForm

"""
Referencing the User model

If you reference User directly (for example, by referring to it in a foreign key)
your code will not work in projects where the AUTH_USER_MODEL setting has been changed
to a different user model.

get_user_model()
Instead of referring to User directly, you should reference the user model using
django.contrib.auth.get_user_model(). This method will return the currently active
user model – the custom user model if one is specified, or User otherwise.

When you define a foreign key or many-to-many relations to the user model
you should specify the custom model using the AUTH_USER_MODEL setting.
"""

CustomUser = get_user_model()


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    fieldsets = UserAdmin.fieldsets + (
        (
            "Profile",
            {
                "fields": ("location", "bio", "personal_website"),
            },
        ),
    )  # type: ignore
    list_display = (
        "email",
        "username",
        "is_staff",
        "location",
        "bio",
        "personal_website",
    )
