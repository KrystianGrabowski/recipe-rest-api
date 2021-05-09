from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


class PublicIngredientsApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_ingredients_unavailable_to_unauthenticated_users(self):
        response = self.client.get(INGREDIENTS_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'example@example.com',
            'password'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients_list(self):
        Ingredient.objects.create(
            user=self.user,
            name='Kale'
        )
        Ingredient.objects.create(
            user=self.user,
            name='Carrot'
        )

        response = self.client.get(INGREDIENTS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(response.data, serializer.data)

    def test_retrieve_ingredients_list_for_user(self):
        Ingredient.objects.create(
            user=self.user,
            name='Kale'
        )

        other_user = get_user_model().objects.create_user(
            'other@example.com',
            'password'
        )
        Ingredient.objects.create(
            user=other_user,
            name='Carrot'
        )

        response = self.client.get(INGREDIENTS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Kale')

    def test_create_ingredient(self):
        payload = {'name': 'Cabbage'}

        self.client.post(INGREDIENTS_URL, payload)

        ingredient_exists = Ingredient.objects\
            .filter(user=self.user, name=payload['name']).exists()

        self.assertTrue(ingredient_exists)

    def test_create_ingredient_invalid(self):
        payload = {'name': ''}

        response = self.client.post(INGREDIENTS_URL, payload)

        ingredient_exists = Ingredient.objects\
            .filter(user=self.user, name=payload['name']).exists()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(ingredient_exists)

    def test_retrieve_ingredients_assigned_to_recipes(self):
        ingredient_1 = Ingredient.objects.create(user=self.user, name='Pasta')
        ingredient_2 = Ingredient.objects\
            .create(user=self.user, name='Tomatoes')
        recipe = Recipe.objects.create(
            title='Spaghetti',
            time=20,
            price=14.00,
            user=self.user
        )

        recipe.ingredients.add(ingredient_1)

        response = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})
        serializer_1 = IngredientSerializer(ingredient_1)
        serializer_2 = IngredientSerializer(ingredient_2)

        self.assertIn(serializer_1.data, response.data)
        self.assertNotIn(serializer_2.data, response.data)

    def test_retrieve_ingredients_assigned_unique(self):
        ingredient = Ingredient.objects.create(user=self.user, name='Flour')
        Ingredient.objects.create(user=self.user, name='Banana')
        recipe_1 = Recipe.objects.create(
            title='Pancakes',
            time=4,
            price=30.0,
            user=self.user
        )
        recipe_1.ingredients.add(ingredient)
        recipe_2 = Recipe.objects.create(
            title='Eggs',
            time=4,
            price=20.0,
            user=self.user
        )
        recipe_2.ingredients.add(ingredient)

        response = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        self.assertEqual(len(response.data), 1)
