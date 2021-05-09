from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe
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

    def test_retrieve_tags_assigned_to_recipes(self):
        tag_1 = Tag.objects.create(user=self.user, name='Dinner')
        tag_2 = Tag.objects.create(user=self.user, name='Vegan')
        recipe = Recipe.objects.create(
            title='Bacon Eggs',
            time=10,
            price=4.00,
            user=self.user
        )

        recipe.tags.add(tag_1)

        response = self.client.get(TAGS_URL, {'assigned_only': 1})
        serializer_1 = TagSerializer(tag_1)
        serializer_2 = TagSerializer(tag_2)

        self.assertIn(serializer_1.data, response.data)
        self.assertNotIn(serializer_2.data, response.data)

    def test_retrieve_tags_assigned_unique(self):
        tag = Tag.objects.create(user=self.user, name='Breakfast')
        Tag.objects.create(user=self.user, name='Dinner')
        recipe_1 = Recipe.objects.create(
            title='Pancakes',
            time=4,
            price=30.0,
            user=self.user
        )
        recipe_1.tags.add(tag)
        recipe_2 = Recipe.objects.create(
            title='Eggs',
            time=4,
            price=20.0,
            user=self.user
        )
        recipe_2.tags.add(tag)

        response = self.client.get(TAGS_URL, {'assigned_only': 1})

        self.assertEqual(len(response.data), 1)
