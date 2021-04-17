from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse


class AdminSiteTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email='admin@example.com',
            password='password123'
        )
        self.client.force_login(self.admin_user)

        self.regular_user = get_user_model().objects.create_user(
            email='user@example.com',
            password='password321',
            name='Test user full name'
        )

    def test_user_listed(self):
        url = reverse('admin:core_user_changelist')
        response = self.client.get(url)

        self.assertContains(response, self.regular_user.name)
        self.assertContains(response, self.regular_user.email)

    def test_user_change_page(self):
        url = reverse('admin:core_user_change', args=[self.regular_user.id])
        result = self.client.get(url)

        self.assertEqual(result.status_code, 200)

    def test_create_user_page(self):
        url = reverse('admin:core_user_add')
        result = self.client.get(url)

        self.assertEqual(result.status_code, 200)
