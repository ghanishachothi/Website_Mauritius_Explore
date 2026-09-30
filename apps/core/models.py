from django.db import models


class NavLink(models.Model):
    """One link in the shared navbar. Ordered by 'order'; drag order in /admin/."""

    label = models.CharField(max_length=50, help_text='Text shown in the navbar, e.g. Experience Insight')
    url_name = models.CharField(max_length=100,
        help_text="Django URL name, e.g. 'experiences:experience_insight' or 'core:home'")
    order = models.PositiveIntegerField(default=0, help_text='Lower numbers show first')
    is_active = models.BooleanField(default=True, help_text='Untick to hide this link from the navbar')

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.label


class SocialLink(models.Model):
    """One round social icon in the shared footer (Stay Connected column)."""

    ICON_CHOICES = [
        ('facebook', 'Facebook'),
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
        ('instagram', 'Instagram'),
        ('tiktok', 'TikTok'),
        ('youtube', 'YouTube'),
        ('linkedin', 'LinkedIn'),
        ('x-twitter', 'X (Twitter)'),
    ]

    platform = models.CharField(max_length=20, choices=ICON_CHOICES,
        help_text='Which icon + brand colour to show')
    url = models.CharField(max_length=300,
        help_text="Link to open, e.g. https://wa.me/23051234567 or mailto:info@mauritiusexplore.com")
    order = models.PositiveIntegerField(default=0, help_text='Lower numbers show first')
    is_active = models.BooleanField(default=True, help_text='Untick to hide this icon')

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.get_platform_display()

    @property
    def icon_class(self):
        """Font Awesome classes for the footer icon."""
        return {
            'facebook': 'fa-brands fa-facebook-f',
            'whatsapp': 'fa-brands fa-whatsapp',
            'email': 'fa-solid fa-envelope',
            'instagram': 'fa-brands fa-instagram',
            'tiktok': 'fa-brands fa-tiktok',
            'youtube': 'fa-brands fa-youtube',
            'linkedin': 'fa-brands fa-linkedin-in',
            'x-twitter': 'fa-brands fa-x-twitter',
        }.get(self.platform, 'fa-solid fa-link')


class LegalLink(models.Model):
    """One link in the shared footer Legal column (Privacy Policy, Terms...)."""

    label = models.CharField(max_length=80, help_text='Text shown, e.g. Privacy Policy')
    url = models.CharField(max_length=300, blank=True,
        help_text="Full URL or path, e.g. /privacy/. Leave empty for a placeholder '#'")
    order = models.PositiveIntegerField(default=0, help_text='Lower numbers show first')
    is_active = models.BooleanField(default=True, help_text='Untick to hide this link')

    class Meta:
        ordering = ['order', 'id']
        verbose_name_plural = 'legal links'

    def __str__(self):
        return self.label


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=150)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name}: {self.subject}'
