from django.core.management.base import BaseCommand

from apps.destinations.models import Guide, Package


class Command(BaseCommand):
    help = "Creates starter Guide and Package rows (Aliyah, John, and their packages)."

    def handle(self, *args, **options):
        aliyah, _ = Guide.objects.update_or_create(
            slug="aliyah-c",
            defaults=dict(
                name="Aliyah C.",
                role="Marine Biology Expert",
                bio="Local ocean lover leading sustainable snorkeling tours in Blue Bay "
                    "Marine Park and catamaran sails to eastern islets.",
                languages="English, French",
                years_experience=6,
                rating=4.9,
                review_count=85,
                specialities="Snorkeling, Cruises, Marine life",
            ),
        )

        john, _ = Guide.objects.update_or_create(
            slug="john-w",
            defaults=dict(
                name="John W.",
                role="Cultural Historian",
                bio="John has 8+ years of guiding travelers through Mauritius's cultural "
                    "heritage and local architecture.",
                languages="English, French",
                years_experience=8,
                rating=4.8,
                review_count=120,
                specialities="History, Museum, Architecture",
            ),
        )

        Package.objects.update_or_create(
            slug="underwater-adventure",
            defaults=dict(
                title="Underwater Adventure",
                guide=aliyah,
                description="Discover the lagoon's coral gardens and marine life on a "
                             "submarine safari and underwater scooter trek, then enjoy a "
                             "seafood lunch on an islet.",
                price=4500,
                duration="1.5 hours",
                rating=5.0,
                review_count=64,
                location="Blue Bay Marine Park",
                difficulty="Easy",
                max_people=10,
                includes="Local seafood lunch served on islet\nSubmarine safari & scooter trek",
                tags="snorkeling, marine-life",
            ),
        )

        Package.objects.update_or_create(
            slug="bois-cheri-tea-route",
            defaults=dict(
                title="Bois Chéri Tea Route & Tasting Tour",
                guide=john,
                description="Follow the tea route through the Bois Chéri plantation, visit "
                             "the museum and factory, and finish with a tasting overlooking "
                             "the south coast.",
                price=1800,
                duration="3 hours",
                rating=4.5,
                review_count=48,
                location="Bois Chéri, South Mauritius",
                difficulty="Easy",
                max_people=15,
                includes="Tea Plantation Tour\nMuseum entry & factory visit\nPanoramic tea tasting session",
                tags="tea-tasting, heritage",
            ),
        )

        self.stdout.write(self.style.SUCCESS(
            "Seeded 2 guides (Aliyah C., John W.) and 2 packages. "
            "Edit or add more any time in /admin/."
        ))
