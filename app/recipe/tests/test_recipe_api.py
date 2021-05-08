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

    def test_create_basic_recipe(self):
        payload = {
            'title': 'spaghetti',
            'time': 20,
            'price': 15.54
        }

        response = self.client.post(RECIPES_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=response.data['id'])

        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time, payload['time'])
        self.assertEqual(float(recipe.price), payload['price'])

    def test_create_recipe_with_tags(self):
        tag_1 = sample_tag(user=self.user, name='Tag 1')
        tag_2 = sample_tag(user=self.user, name='Tag 2')

        payload = {
            'title': 'Tasty food',
            'tags': [tag_2.id, tag_1.id],
            'time': 30,
            'price': 7.00
        }

        response = self.client.post(RECIPES_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=response.data['id'])
        tags = recipe.tags.all()

        self.assertEqual(tags.count(), 2)
        self.assertIn(tag_1, tags)
        self.assertIn(tag_2, tags)

    def test_create_recipe_with_ingredients(self):
        ingredient_1 = sample_ingredient(user=self.user, name='Ginger')
        ingredient_2 = sample_ingredient(user=self.user, name='Prawns')
        payload = {
            'title': 'Chicken breasts with potatoes in tomato sauce',
            'ingredients': [ingredient_2.id, ingredient_1.id],
            'time': 48,
            'price': 21.99
        }

        response = self.client.post(RECIPES_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=response.data['id'])
        ingredients = recipe.ingredients.all()

        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient_1, ingredients)
        self.assertIn(ingredient_2, ingredients)

    def test_partial_update_recipe(self):
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))

        new_tag = sample_tag(user=self.user, name='Poor')

        payload = {
            'title': 'New title',
            'tags': [new_tag.id]
        }

        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()

        self.assertEqual(recipe.title, payload['title'])

        tags = recipe.tags.all()

        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        payload = {
            'title': 'Fully new title',
            'time': 66,
            'price': 5.00
        }

        url = detail_url(recipe.id)
        self.client.put(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time, payload['time'])
        self.assertEqual(recipe.price, payload['price'])

        tags = recipe.tags.all()
        self.assertEqual(len(tags), 0)
