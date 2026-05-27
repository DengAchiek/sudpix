import base64
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from apps.cart.models import CartItem
from apps.downloads.models import Download
from apps.media_management.models import MediaAsset
from apps.payments.models import Payment
from apps.projects.models import (
    FinalDelivery,
    Project,
    ProjectApproval,
    ProjectBrief,
    ProjectFeedback,
    ProjectMilestone,
    RevisionRequest,
)

TINY_GIF = base64.b64decode("R0lGODdhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==")


class Command(BaseCommand):
    help = "Create repeatable demo data for the SudPix client portal."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="mary_wanjiku")
        parser.add_argument("--password", default="SudpixDemo123!")
        parser.add_argument("--email", default="mary@example.com")
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete the existing demo user's portal data before reseeding.",
        )

    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]
        email = options["email"]

        user = self.get_or_create_demo_user(username=username, password=password, email=email)

        if options["reset"]:
            self.reset_demo_data(user)

        projects = self.seed_projects(user)
        media_assets = self.seed_media_assets(projects)
        self.seed_cart(user, media_assets)
        payments = self.seed_payments(user, projects, media_assets)
        downloads = self.seed_downloads(user, projects, payments)
        self.seed_workspaces(user, projects, media_assets)

        self.stdout.write(self.style.SUCCESS("SudPix demo portal data is ready."))
        self.stdout.write(f"Username: {username}")
        self.stdout.write(f"Password: {password}")
        self.stdout.write(f"Projects: {len(projects)}")
        self.stdout.write(f"Media files: {len(media_assets)}")
        self.stdout.write(f"Payments: {len(payments)}")
        self.stdout.write(f"Downloads: {len(downloads)}")
        self.stdout.write("Workspaces: briefs, milestones, review, and delivery seeded")

    def get_or_create_demo_user(self, *, username, password, email):
        user_model = get_user_model()
        user, _ = user_model.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "first_name": "Mary",
                "last_name": "Wanjiku",
            },
        )
        user.email = email
        if not user.first_name:
            user.first_name = "Mary"
        if not user.last_name:
            user.last_name = "Wanjiku"
        user.set_password(password)
        user.save()
        return user

    def reset_demo_data(self, user):
        CartItem.objects.filter(user=user).delete()
        Download.objects.filter(user=user).delete()
        Payment.objects.filter(user=user).delete()
        Project.objects.filter(client=user).delete()

    def seed_projects(self, user):
        project_specs = [
            {
                "title": "Wedding Shoot",
                "slug": "wedding-shoot",
                "service_type": "Photography",
                "status": Project.Status.READY,
                "shoot_date": date(2026, 3, 23),
                "description": "Preview your wedding gallery, select favorites, and unlock the final downloads after payment verification.",
                "cover_image_url": "https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&w=1200&q=80",
            },
            {
                "title": "Brand Campaign",
                "slug": "brand-campaign",
                "service_type": "Branding",
                "status": Project.Status.IN_REVIEW,
                "shoot_date": date(2026, 3, 16),
                "description": "Track branding deliverables, review approved assets, and download the final campaign pack when it is ready.",
                "cover_image_url": "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=1200&q=80",
            },
            {
                "title": "Event Recap Film",
                "slug": "event-recap-film",
                "service_type": "Videography",
                "status": Project.Status.PROCESSING,
                "shoot_date": date(2026, 3, 10),
                "description": "Monitor video edit progress and check for released highlight clips and final files.",
                "cover_image_url": "https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?auto=format&fit=crop&w=1200&q=80",
            },
        ]

        projects = []
        for spec in project_specs:
            project, _ = Project.objects.update_or_create(
                client=user,
                slug=spec["slug"],
                defaults=spec,
            )
            projects.append(project)

        return projects

    def seed_media_assets(self, projects):
        project_map = {project.slug: project for project in projects}
        asset_specs = [
            {
                "project": project_map["wedding-shoot"],
                "title": "Bridal Portrait 01.jpg",
                "kind": MediaAsset.Kind.PHOTO,
                "price": Decimal("80.00"),
                "preview_image_url": "https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&w=900&q=80",
                "is_highlight": True,
            },
            {
                "project": project_map["wedding-shoot"],
                "title": "Reception Highlight.mp4",
                "kind": MediaAsset.Kind.VIDEO,
                "price": Decimal("500.00"),
                "preview_image_url": "https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?auto=format&fit=crop&w=900&q=80",
                "is_highlight": True,
            },
            {
                "project": project_map["brand-campaign"],
                "title": "Brand Cover Mockup.png",
                "kind": MediaAsset.Kind.DESIGN,
                "price": Decimal("300.00"),
                "preview_image_url": "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=900&q=80",
                "is_edited": True,
            },
            {
                "project": project_map["brand-campaign"],
                "title": "Launch Poster Pack.pdf",
                "kind": MediaAsset.Kind.DOCUMENT,
                "price": Decimal("200.00"),
                "preview_image_url": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=900&q=80",
                "is_edited": True,
            },
            {
                "project": project_map["event-recap-film"],
                "title": "Event Recap Master.mp4",
                "kind": MediaAsset.Kind.VIDEO,
                "price": Decimal("500.00"),
                "preview_image_url": "https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?auto=format&fit=crop&w=900&q=80",
            },
        ]

        assets = []
        for spec in asset_specs:
            project = spec["project"]
            title = spec["title"]
            defaults = {key: value for key, value in spec.items() if key not in {"project", "title"}}
            asset, _ = MediaAsset.objects.update_or_create(
                project=project,
                title=title,
                defaults=defaults,
            )
            self.attach_demo_preview(asset)
            self.attach_demo_asset_file(asset)
            assets.append(asset)

        return assets

    def seed_cart(self, user, assets):
        selected_titles = {"Bridal Portrait 01.jpg", "Event Recap Master.mp4"}
        for asset in assets:
            if asset.title in selected_titles:
                CartItem.objects.get_or_create(user=user, media_asset=asset)

    def seed_payments(self, user, projects, media_assets):
        project_map = {project.slug: project for project in projects}
        asset_map = {asset.title: asset for asset in media_assets}
        now = timezone.now()

        payment_specs = [
            {
                "reference": "SUDPIX-DEMO-001",
                "project": project_map["wedding-shoot"],
                "amount": Decimal("580.00"),
                "method": Payment.Method.MPESA,
                "status": Payment.Status.CONFIRMED,
                "phone_number": "254700000000",
                "paid_at": now,
                "asset_titles": ["Bridal Portrait 01.jpg", "Reception Highlight.mp4"],
            },
            {
                "reference": "SUDPIX-DEMO-002",
                "project": project_map["event-recap-film"],
                "amount": Decimal("500.00"),
                "method": Payment.Method.CARD,
                "status": Payment.Status.PENDING,
                "phone_number": "",
                "paid_at": None,
                "asset_titles": ["Event Recap Master.mp4"],
            },
        ]

        payments = []
        for spec in payment_specs:
            reference = spec["reference"]
            asset_titles = spec["asset_titles"]
            defaults = {**spec, "user": user}
            defaults.pop("asset_titles")
            payment, _ = Payment.objects.update_or_create(
                user=user,
                reference=reference,
                defaults=defaults,
            )
            payment.media_assets.set(
                [asset_map[title] for title in asset_titles if title in asset_map]
            )
            payments.append(payment)

        return payments

    def seed_downloads(self, user, projects, payments):
        project_map = {project.slug: project for project in projects}
        payment_map = {payment.reference: payment for payment in payments}
        now = timezone.now()

        download_specs = [
            {
                "title": "Wedding Photo Pack.zip",
                "project": project_map["wedding-shoot"],
                "payment": payment_map["SUDPIX-DEMO-001"],
                "description": "A bundled archive containing the wedding gallery files unlocked after payment confirmation.",
                "status": Download.Status.READY,
                "file_url": "https://example.com/downloads/wedding-photo-pack.zip",
                "available_at": now,
            },
            {
                "title": "Brand Campaign Final Pack.zip",
                "project": project_map["event-recap-film"],
                "payment": payment_map["SUDPIX-DEMO-002"],
                "description": "Final recap assets prepared for delivery after payment confirmation.",
                "status": Download.Status.PROCESSING,
                "file_url": "",
                "available_at": None,
            },
        ]

        downloads = []
        for spec in download_specs:
            title = spec["title"]
            defaults = {**spec, "user": user}
            download, _ = Download.objects.update_or_create(
                user=user,
                title=title,
                defaults=defaults,
            )
            self.attach_demo_download_file(download)
            downloads.append(download)

        return downloads

    def seed_workspaces(self, user, projects, media_assets):
        project_map = {project.slug: project for project in projects}
        asset_map = {asset.title: asset for asset in media_assets}
        now = timezone.now()

        brief_specs = {
            "wedding-shoot": {
                "objective": "Capture an elegant, documentary-led wedding story for the couple and family archive.",
                "audience": "Couple, family, and invited guests",
                "deliverables": "Curated JPG photo gallery, highlight reel, and downloadable archive.",
                "creative_direction": "Warm light, natural moments, refined portraits, and a cinematic reception finish.",
                "reference_links": "Golden-hour portraits and editorial reception details.",
            },
            "brand-campaign": {
                "objective": "Create a confident visual identity launch pack for a Nairobi lifestyle brand.",
                "audience": "Launch customers and retail partners",
                "deliverables": "Logo lockups, launch poster set, brand deck, and social templates.",
                "creative_direction": "Premium minimal layouts with bold accent colour and strong product focus.",
                "reference_links": "Reference board approved during discovery.",
            },
            "event-recap-film": {
                "objective": "Deliver an energetic recap film for post-event social promotion.",
                "audience": "Attendees and online event community",
                "deliverables": "Master MP4 film and vertical reel cutdowns.",
                "creative_direction": "Fast opening sequence, speaker moments, and audience energy.",
                "reference_links": "",
            },
        }
        for slug, defaults in brief_specs.items():
            ProjectBrief.objects.update_or_create(project=project_map[slug], defaults=defaults)

        milestone_specs = {
            "wedding-shoot": [
                ("Brief received", ProjectMilestone.Status.COMPLETED),
                ("Date confirmed", ProjectMilestone.Status.COMPLETED),
                ("Shoot completed", ProjectMilestone.Status.COMPLETED),
                ("Gallery uploaded", ProjectMilestone.Status.COMPLETED),
                ("Client selections made", ProjectMilestone.Status.COMPLETED),
                ("Payment completed", ProjectMilestone.Status.COMPLETED),
                ("Final downloads unlocked", ProjectMilestone.Status.COMPLETED),
            ],
            "brand-campaign": [
                ("Brief received", ProjectMilestone.Status.COMPLETED),
                ("Concept direction prepared", ProjectMilestone.Status.COMPLETED),
                ("Logo presentation uploaded", ProjectMilestone.Status.ACTIVE),
                ("Client approval", ProjectMilestone.Status.UPCOMING),
                ("Final brand files delivered", ProjectMilestone.Status.UPCOMING),
            ],
            "event-recap-film": [
                ("Brief received", ProjectMilestone.Status.COMPLETED),
                ("Shoot completed", ProjectMilestone.Status.COMPLETED),
                ("First edit in progress", ProjectMilestone.Status.ACTIVE),
                ("Client review", ProjectMilestone.Status.UPCOMING),
                ("Final downloads unlocked", ProjectMilestone.Status.UPCOMING),
            ],
        }
        for slug, entries in milestone_specs.items():
            for display_order, (title, status) in enumerate(entries, start=1):
                ProjectMilestone.objects.update_or_create(
                    project=project_map[slug],
                    title=title,
                    defaults={
                        "display_order": display_order,
                        "status": status,
                        "completed_at": now if status == ProjectMilestone.Status.COMPLETED else None,
                    },
                )

        ProjectApproval.objects.update_or_create(
            project=project_map["wedding-shoot"],
            defaults={
                "decision": ProjectApproval.Decision.APPROVED,
                "note": "The final wedding gallery and reel are approved for delivery.",
                "decided_by": user,
                "decided_at": now,
            },
        )
        ProjectApproval.objects.update_or_create(
            project=project_map["brand-campaign"],
            defaults={
                "decision": ProjectApproval.Decision.REVISIONS_REQUESTED,
                "note": "Please explore a more compact logo lockup for social avatars.",
                "decided_by": user,
                "decided_at": now,
            },
        )
        ProjectApproval.objects.update_or_create(
            project=project_map["event-recap-film"],
            defaults={"decision": ProjectApproval.Decision.PENDING},
        )

        FinalDelivery.objects.update_or_create(
            project=project_map["wedding-shoot"],
            defaults={
                "status": FinalDelivery.Status.RELEASED,
                "summary": "High-resolution photos and the reception highlight film are ready for secure download.",
                "release_note": "Payment confirmed through M-PESA. Final files are unlocked.",
                "released_at": now,
            },
        )
        FinalDelivery.objects.update_or_create(
            project=project_map["brand-campaign"],
            defaults={
                "status": FinalDelivery.Status.READY,
                "summary": "Brand concepts are ready for client review and approval.",
            },
        )
        FinalDelivery.objects.update_or_create(
            project=project_map["event-recap-film"],
            defaults={
                "status": FinalDelivery.Status.PREPARING,
                "summary": "The master recap film is in post-production.",
            },
        )

        ProjectFeedback.objects.update_or_create(
            project=project_map["brand-campaign"],
            author=user,
            message="The direction feels premium. Could the mark remain readable in a smaller social icon?",
            defaults={
                "area": ProjectFeedback.Area.GALLERY,
                "studio_reply": "Yes. We will prepare a compact lockup in the next revision round.",
            },
        )
        RevisionRequest.objects.update_or_create(
            project=project_map["brand-campaign"],
            requested_by=user,
            title="Compact social logo lockup",
            defaults={
                "media_asset": asset_map["Brand Cover Mockup.png"],
                "details": "Provide a reduced version optimized for profile images and mobile headers.",
                "status": RevisionRequest.Status.IN_PROGRESS,
                "studio_response": "Revision is underway and will be added to final delivery.",
            },
        )

    def attach_demo_preview(self, asset):
        if asset.preview_image:
            return

        filename = f"demo/previews/{slugify(asset.title) or 'preview'}.gif"
        asset.preview_image.save(filename, ContentFile(TINY_GIF), save=True)

    def attach_demo_asset_file(self, asset):
        if asset.file:
            return

        extension = asset.title.rsplit(".", 1)[-1].lower() if "." in asset.title else "txt"
        filename = f"demo/assets/{slugify(asset.title) or 'asset'}.{extension}"
        content = f"Demo asset for {asset.title}\nProject: {asset.project.title}\n".encode()
        asset.file.save(filename, ContentFile(content), save=True)

    def attach_demo_download_file(self, download):
        if download.file or download.status != Download.Status.READY:
            return

        filename = f"demo/downloads/{slugify(download.title) or 'download'}.zip"
        content = f"Demo download archive for {download.title}\n".encode()
        download.file.save(filename, ContentFile(content), save=True)
