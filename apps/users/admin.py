from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = True
    extra = 0


class CustomUserAdmin(UserAdmin):
    inlines = [ProfileInline]


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'deletion_requested', 'phone_number', 'created_at')
    list_filter = ('deletion_requested', 'created_at')
    list_editable = ('deletion_requested',)
    actions = ['approve_deletion']

    @admin.action(description='Approve account deletion (Delete User)')
    def approve_deletion(self, request, queryset):
        deleted_count = 0
        for profile in queryset:
            profile.user.delete()  # Deleting User also deletes Profile via CASCADE
            deleted_count += 1
        self.message_user(request, f"Successfully approved and deleted {deleted_count} account(s).")