from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_recipe(user, **kwargs):
    defaults = {
        'title': 'Sample recipe',
        'time': 10,
        'price': 12.06
    }

    defaults.update(kwargs)

    return Recipe.objects.create(user=user, **defaults)


def sample_tag(user, name='Sample tag'):
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Sample ingredient'):
    return Ingredient.objects.create(user=user, name=name)


class PublicRecipeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_authentication_is_required(self):
        response = self.client.get(RECIPES_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='example@example.com',
            password='password'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        response = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_recipes_limited_to_user(self):
        other_user = get_user_model().objects.create_user(
            email='other_example@example.com',
            password='password'
        )

        sample_recipe(user=self.user)
        sample_recipe(user=other_user)

        response = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_view_recipe_detail(self):
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        response = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(response.data, serializer.data)
