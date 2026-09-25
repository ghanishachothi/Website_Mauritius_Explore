from django.conf import settings
from django.db import models


class Profile(models.Model):
    """Extra info for every user. Created automatically (see signals.py)."""

    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        CUSTOMER = 'customer', 'Customer'
        VIEWER = 'viewer', 'Viewer'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.CUSTOMER)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} ({self.get_role_display()})'

    @property
    def can_book(self):
        """Viewers can browse only; customers and admins can book."""
        return self.role in (self.Role.ADMIN, self.Role.CUSTOMER)
