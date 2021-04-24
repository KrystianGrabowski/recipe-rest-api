from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag
from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


class PublicTagsApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        response = self.client.get(TAGS_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'example@example.com',
            'password'
        )

        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tag_list(self):
        Tag.objects.create(user=self.user, name='Ketogenic')
        Tag.objects.create(user=self.user, name='Vegan')

        response = self.client.get(TAGS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(response.data, serializer.data)

    def test_retrieve_tag_list_limited_to_user(self):
        Tag.objects.create(user=self.user, name='Ketogenic')
        Tag.objects.create(user=self.user, name='Vegan')

        other_user = get_user_model().objects.create_user(
            'other@example.com'
            'password'
        )
        Tag.objects.create(user=other_user, name='ShouldNotSeeTag')

        response = self.client.get(TAGS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(
            [response.data[0]['name'], response.data[1]['name']],
            ['Vegan', 'Ketogenic']
        )

    def test_create_tag(self):
        payload = {'name': 'newTag'}
        self.client.post(TAGS_URL, payload)

        tag_exists = Tag.objects\
            .filter(user=self.user, name=payload['name']).exists()

        self.assertTrue(tag_exists)

    def test_create_tag_invalid(self):
        payload = {'name': ''}
        response = self.client.post(TAGS_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        tag_exists = Tag.objects\
            .filter(user=self.user, name=payload['name']).exists()

        self.assertFalse(tag_exists)
