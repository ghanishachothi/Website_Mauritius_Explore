from django.conf import settings
from django.db import models


class Profile(models.Model):

    class AuthProvider(models.TextChoices):
        EMAIL = 'email', 'Email'
        GOOGLE = 'google', 'Google'
        FACEBOOK = 'facebook', 'Facebook'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(blank=True, default='')
    gender = models.CharField(max_length=20, blank=True, default='')
    language = models.CharField(max_length=100, blank=True, default='')
    phone_number = models.CharField(max_length=20, blank=True, default='')
    nationality = models.CharField(max_length=100, blank=True, default='')
    deletion_requested = models.BooleanField(default=False)

    provider = models.CharField(
        max_length=10,
        choices=AuthProvider.choices,
        default=AuthProvider.EMAIL
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} ({"Admin" if self.user.is_staff else "Customer"})'

    @property
    def phone(self):
        """Alias for phone_number to prevent breakage in external views accessing .phone."""
        return self.phone_number