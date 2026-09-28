from django.conf import settings
from django.db import models


class Profile(models.Model):
    """Extra info for every user. Created automatically via signals."""

    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        CUSTOMER = 'customer', 'Customer'
        VIEWER = 'viewer', 'Viewer'

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
    reminders = models.BooleanField(default=False)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.CUSTOMER)
    deletion_requested = models.BooleanField(default=False)
    
    provider = models.CharField(
        max_length=10,
        choices=AuthProvider.choices,
        default=AuthProvider.EMAIL
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} ({self.get_role_display()})'

    @property
    def can_book(self):
        """Viewers can browse only; customers and admins can book."""
        return self.role in (self.Role.ADMIN, self.Role.CUSTOMER)