from django.test import TestCase
from django.urls import reverse


class PortfolioPageTests(TestCase):
    def test_portfolio_page_renders(self):
        response = self.client.get(reverse("portfolio:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("portfolio:detail", args=["wedding-story"]))

    def test_portfolio_detail_page_renders(self):
        response = self.client.get(reverse("portfolio:detail", args=["live-event-film"]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Live Event Film")
        self.assertContains(response, "Videography Portfolio")
        self.assertContains(
            response,
            f'{reverse("bookings:create")}?service=Videography',
            html=False,
        )

    def test_unknown_portfolio_detail_returns_404(self):
        response = self.client.get(reverse("portfolio:detail", args=["unknown-project"]))

        self.assertEqual(response.status_code, 404)
