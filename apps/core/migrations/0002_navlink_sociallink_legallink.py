from django.db import migrations, models


def seed_defaults(apps, schema_editor):
    """Create the standard navbar + footer rows so nothing is hardcoded in templates."""
    NavLink = apps.get_model('core', 'NavLink')
    SocialLink = apps.get_model('core', 'SocialLink')
    LegalLink = apps.get_model('core', 'LegalLink')

    if NavLink.objects.exists():
        return
    nav = [
        ('Discover Mauritius', 'core:home'),
        ('Experience Insight', 'experiences:experience_insight'),
        ('Explore The Island', 'explore_island'),
        ('Guides & Packages', 'destinations:guides_packages'),
        ('Island Calendar', 'experiences:island_calendar'),
        ('Explore Board', 'destinations:explore_board'),
        ('Explore Your Way', 'experiences:explore_your_way'),
    ]
    for i, (label, url_name) in enumerate(nav):
        NavLink.objects.create(label=label, url_name=url_name, order=i)

    if SocialLink.objects.exists():
        return
    social = [
        ('facebook', 'https://www.facebook.com/'),
        ('whatsapp', 'https://wa.me/'),
        ('email', 'mailto:info@mauritiusexplore.com'),
        ('instagram', 'https://www.instagram.com/'),
    ]
    for i, (platform, url) in enumerate(social):
        SocialLink.objects.create(platform=platform, url=url, order=i)

    if LegalLink.objects.exists():
        return
    legal = [('Privacy Policy', ''), ('Terms of Service', '')]
    for i, (label, url) in enumerate(legal):
        LegalLink.objects.create(label=label, url=url, order=i)


def unseed(apps, schema_editor):
    apps.get_model('core', 'NavLink').objects.all().delete()
    apps.get_model('core', 'SocialLink').objects.all().delete()
    apps.get_model('core', 'LegalLink').objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='NavLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(help_text='Text shown in the navbar, e.g. Experience Insight', max_length=50)),
                ('url_name', models.CharField(help_text="Django URL name, e.g. 'experiences:experience_insight' or 'core:home'", max_length=100)),
                ('order', models.PositiveIntegerField(default=0, help_text='Lower numbers show first')),
                ('is_active', models.BooleanField(default=True, help_text='Untick to hide this link from the navbar')),
            ],
            options={
                'ordering': ['order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='SocialLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform', models.CharField(choices=[('facebook', 'Facebook'), ('whatsapp', 'WhatsApp'), ('email', 'Email'), ('instagram', 'Instagram'), ('tiktok', 'TikTok'), ('youtube', 'YouTube'), ('linkedin', 'LinkedIn'), ('x-twitter', 'X (Twitter)')], help_text='Which icon + brand colour to show', max_length=20)),
                ('url', models.CharField(help_text='Link to open, e.g. https://wa.me/23051234567 or mailto:info@mauritiusexplore.com', max_length=300)),
                ('order', models.PositiveIntegerField(default=0, help_text='Lower numbers show first')),
                ('is_active', models.BooleanField(default=True, help_text='Untick to hide this icon')),
            ],
            options={
                'ordering': ['order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='LegalLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(help_text='Text shown, e.g. Privacy Policy', max_length=80)),
                ('url', models.CharField(blank=True, help_text="Full URL or path, e.g. /privacy/. Leave empty for a placeholder '#'", max_length=300)),
                ('order', models.PositiveIntegerField(default=0, help_text='Lower numbers show first')),
                ('is_active', models.BooleanField(default=True, help_text='Untick to hide this link')),
            ],
            options={
                'ordering': ['order', 'id'],
                'verbose_name_plural': 'legal links',
            },
        ),
        migrations.RunPython(seed_defaults, unseed),
    ]
