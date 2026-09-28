"""
Shared site frame content: header, side menu, footer, social icons, app badges, months.
Everyone gets exactly this when they run: python manage.py migrate
"""
from django.db import migrations

HEADER = [  # name, url, set, line 1, line 2
    ("Discover Mauritius", "/", "header1", "Discover", "Mauritius"),
    ("Experience Insight", "/experiences/", "header1", "Experience", "Insight"),
    ("Explore The Island", "/destinations/", "header1", "Explore", "The Island"),
    ("Guides & Packages", "/destinations/guides-packages/", "header1", "Guides &", "Packages"),
    ("Island Calendar", "/experiences/calendar/", "header1", "Island", "Calendar"),
    ("Explore Board", "/destinations/board/", "header2", "Explore", "Board"),
    ("Explore Your Way", "/experiences/", "header2", "Explore", "Your Way"),
]
SIDE = [  # name, url, icon
    ("My Experiences", "/experiences/my-experiences/", "ticket"),
    ("My Profile", "/accounts/profile/", "user"),
    ("Help & Contact", "#help", "help"),
]
EV, GP, BD = "/experiences/", "/destinations/guides-packages/", "/destinations/board/"
FOOTER = {
    "Explore Mauritius": [("Discover Mauritius", "/"), ("Explore Experiences", EV),
        ("Top Destinations", "/#top-destinations"), ("Things to Do", EV),
        ("Hidden Gems of Mauritius", BD), ("Island Activities", "/experiences/calendar/"),
        ("Local Attractions", "/destinations/")],
    "Experiences": [("Beach & Water Activities", EV + "?category=water-sports"),
        ("Nature & Adventure", EV + "?category=hiking"), ("Cultural Experiences", EV + "?category=culture"),
        ("Food & Local Cuisine", EV + "?category=food"), ("Hiking & Outdoor Adventures", EV + "?category=hiking"),
        ("Family Activities", EV), ("Romantic Experiences", EV)],
    "Guides": [("Local Guides", GP), ("Find a Guide", GP), ("Explore with Locals", GP),
        ("Guide Recommendations", GP), ("Guided Tours", GP), ("Travel Tips", "#help"),
        ("Useful Information", "#help")],
    "Mauritius Explorer": [("About Us", "#help"), ("Contact Us", "#help"), ("Our Mission", "#help"),
        ("Become a Guide", "#help"), ("Become a Partner", "#help"),
        ("Privacy Policy", "#help"), ("Terms & Conditions", "#help")],
}
SOCIALS = [  # platform, default url (edit the real one in /admin/)
    ("facebook", "https://www.facebook.com/"), ("whatsapp", "https://wa.me/"),
    ("gmail", "mailto:"), ("instagram", "https://www.instagram.com/"),
]
MONTHS = [
    (1, "Hot, green and festive", 30, 27, "Busy", "Hot and humid with tropical showers; cyclone season.", "New Year celebrations and Thaipoosam Cavadee."),
    (2, "Warm sea, lush island", 30, 28, "Moderate", "The hottest, wettest month; cyclones are possible.", "Chinese Spring Festival in Port Louis."),
    (3, "Summer winds down", 29, 28, "Moderate", "Still hot, with fewer showers towards the end.", "Maha Shivaratri pilgrimage to Grand Bassin; Independence Day (12 March)."),
    (4, "Calm and sunny", 28, 27, "Quiet", "Warm days and cooler evenings; rain eases off.", "Ougadi (Telugu New Year) and Easter."),
    (5, "Great for hiking", 26, 26, "Quiet", "Dry, sunny and pleasant - ideal for the trails.", "Labour Day (1 May); the hiking season begins."),
    (6, "Cool and breezy", 24, 25, "Quiet", "Winter starts: cooler, windier, especially in the south.", "Kitesurfing season at Le Morne."),
    (7, "Winter on the island", 24, 24, "Moderate", "Coolest month; sunny on the north and west coasts.", "Humpback whales arrive off the west coast."),
    (8, "Whale watching", 24, 23, "Busy", "Cool and dry, with steady trade winds.", "Whale and dolphin watching; European summer holidays."),
    (9, "Spring is back", 25, 23, "Moderate", "Warming up, dry and sunny.", "Pere Laval pilgrimage (9 September)."),
    (10, "Bright and dry", 26, 24, "Moderate", "One of the driest months; long sunny days.", "Diwali (festival of lights) - date varies, Oct/Nov."),
    (11, "Warm sea again", 28, 25, "Busy", "Hot days and a warm sea; perfect for the beach.", "Diwali and Arrival of Indentured Labourers Day (2 November)."),
    (12, "Summer holidays", 29, 26, "Busy", "Hot and sunny with the first summer showers.", "Christmas, New Year festivities and flamboyant trees in bloom."),
]


def add_site_content(apps, schema_editor):
    SitePage = apps.get_model("core", "SitePage")
    FooterColumn = apps.get_model("core", "FooterColumn")
    FooterLink = apps.get_model("core", "FooterLink")
    SocialLink = apps.get_model("core", "SocialLink")
    AppLink = apps.get_model("core", "AppLink")
    MonthTip = apps.get_model("core", "MonthTip")

    # header + side menu (anything else in the header is removed)
    SitePage.objects.filter(location__in=["header1", "header2"]).exclude(name__in=[h[0] for h in HEADER]).delete()
    for i, (name, url, where, l1, l2) in enumerate(HEADER):
        SitePage.objects.update_or_create(name=name, defaults=dict(
            url=url, location=where, header_line1=l1, header_line2=l2, order=i))
    for i, (name, url, icon) in enumerate(SIDE):
        SitePage.objects.update_or_create(name=name, defaults=dict(
            url=url, location="side", header_line1=name, header_line2="", icon=icon, order=i))

    # footer columns + links
    FooterColumn.objects.exclude(title__in=list(FOOTER)).delete()
    for i, (title, links) in enumerate(FOOTER.items()):
        col, _ = FooterColumn.objects.update_or_create(title=title, defaults={"order": i})
        FooterLink.objects.filter(column=col).exclude(label__in=[l for l, _ in links]).delete()
        for j, (label, url) in enumerate(links):
            FooterLink.objects.update_or_create(column=col, label=label, defaults={"url": url, "order": j})

    # social icons (a real link already saved in /admin/ is kept)
    SocialLink.objects.exclude(platform__in=[p for p, _ in SOCIALS]).delete()
    for i, (platform, url) in enumerate(SOCIALS):
        s, _ = SocialLink.objects.get_or_create(platform=platform, defaults={"url": url})
        s.icon, s.show_in_footer, s.order = f"images/{platform}.png", True, i
        s.save()

    # store badges (a real store link already saved in /admin/ is kept)
    for i, store in enumerate(["google", "apple", "huawei"]):
        AppLink.objects.get_or_create(store=store, defaults={"order": i})

    # "When to come" months (edits made in /admin/ are kept)
    for m, headline, air, sea, crowd, note, highlight in MONTHS:
        MonthTip.objects.get_or_create(month=m, defaults=dict(
            headline=headline, air=air, sea=sea, crowd=crowd, note=note, highlight=highlight))


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_applink_footercolumn_monthtip_sitepage_sociallink_and_more'),
    ]

    operations = [
        migrations.RunPython(add_site_content, migrations.RunPython.noop),
    ]
