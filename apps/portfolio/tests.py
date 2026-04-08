from django.test import TestCase
from django.urls import reverse


class PortfolioPageTests(TestCase):
    def test_portfolio_page_renders(self):
        response = self.client.get(reverse("portfolio:list"))

        self.assertEqual(response.status_code, 200)
