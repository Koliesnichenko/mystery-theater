import os
import tempfile
from http import client

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from theater.models import Play, Actor, Genre, Performance, TheaterHall
from theater.serializers import PlayListSerializer, PlaySerializer, PlayDetailSerializer

PLAY_URL = reverse("theater:play-list")

User = get_user_model()


def sample_actor(**params) -> Actor:
    defaults = {
        "first_name": "John",
        "last_name": "Mitchel",
    }
    defaults.update(params)
    return Actor.objects.create(**defaults)


def sample_genre(**params) -> Genre:
    defaults = {"name": "Drama"}
    defaults.update(params)
    return Genre.objects.create(**defaults)


def sample_play(**params) -> Play:
    defaults = {
        "title": "Test Title",
        "description": "Test Description",
        "duration": 60,
    }
    defaults.update(params)
    return Play.objects.create(**defaults)


def sample_performance(**params) -> Performance:
    theater_hall = TheaterHall.objects.create(
        name="Main Hall", rows=10, seats_in_row=20
    )

    defaults = {
        "show_time": "2025-02-12 12:00:00",
        "play": None,
        "theater_hall": theater_hall,
    }
    defaults.update(params)

    return Performance.objects.create(**defaults)


def detail_url(play_id):
    return reverse("theater:play-detail", args=[play_id])


def image_upload_url(play_id):
    return reverse("theater:play-upload-image", args=[play_id])


class UnauthenticatedPlayApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(PLAY_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_post_required(self):
        response = self.client.post(PLAY_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_delete_required(self):
        response = self.client.delete(PLAY_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedPlayApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", email="test@email.test", password="testpass"
        )
        self.client.force_authenticate(user=self.user)

    def test_play_list(self):
        sample_play()

        res = self.client.get(PLAY_URL)

        plays = Play.objects.order_by("id")
        serializer = PlayListSerializer(plays, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_plays_by_genres(self):
        genre = sample_genre(name="Drama")

        play_with_genre = sample_play()
        play_without_genre = sample_play()
        play_with_genre.genres.add(genre)

        res = self.client.get(PLAY_URL, {"genres": genre.name})

        serializer_with_genre = PlayListSerializer(play_with_genre)
        serializer_without_genre = PlayListSerializer(play_without_genre)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn(serializer_with_genre.data, res.data)
        self.assertNotIn(serializer_without_genre.data, res.data)

    def test_filter_plays_by_actors_first_name(self):
        actor = sample_actor(first_name="Tom", last_name="Cruse")

        play_with_actor = sample_play()
        play_without_actor = sample_play()
        play_with_actor.actors.add(actor)

        res = self.client.get(PLAY_URL, {"actors": actor.first_name})

        serializer_with_actor = PlayListSerializer(play_with_actor)
        serializer_without_actor = PlayListSerializer(play_without_actor)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn(serializer_with_actor.data, res.data)
        self.assertNotIn(serializer_without_actor.data, res.data)

    def test_filter_plays_by_actors_first_last_name(self):
        actor = sample_actor(first_name="Bred", last_name="Pitt")

        play_with_actor = sample_play()
        play_without_actor = sample_play()
        play_with_actor.actors.add(actor)

        res = self.client.get(PLAY_URL, {"actors": actor.last_name})

        serializer_with_actor = PlayListSerializer(play_with_actor)
        serializer_without_actor = PlayListSerializer(play_without_actor)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn(serializer_with_actor.data, res.data)
        self.assertNotIn(serializer_without_actor.data, res.data)

    def test_filter_plays_by_title(self):
        play_with_title = sample_play(title="Test Title")
        play_without_title = sample_play(title="Other Title")

        res = self.client.get(PLAY_URL, {"title": "Test Title"})

        serializer = PlayListSerializer(play_with_title)
        serializer_without_title = PlayListSerializer(play_without_title)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer.data, res.data)
        self.assertNotIn(serializer_without_title.data, res.data)

    def test_filter_plays_by_partial_title(self):
        play_with_title = sample_play(title="Test Title")
        play_without_title = sample_play(title="Other Title")

        res = self.client.get(PLAY_URL, {"title": "Test"})

        serializer = PlayListSerializer(play_with_title)
        serializer_without_title = PlayListSerializer(play_without_title)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer.data, res.data)
        self.assertNotIn(serializer_without_title.data, res.data)

    def test_create_play_forbidden(self):
        payload = {
            "title": "Test Title",
            "description": "Test Description",
            "duration": 60,
        }
        res = self.client.post(PLAY_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_play_detail(self):
        play = sample_play()
        genre = sample_genre(name="Drama")
        actor = sample_actor(first_name="Tom", last_name="Cruse")
        play.genres.add(genre)
        play.actors.add(actor)
        url = detail_url(play.id)
        res = self.client.get(url)
        serializer = PlayDetailSerializer(play)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)


class AdminPlayApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="adminuser",
            email="admin@admin.test",
            password="testpass",
            is_staff=True,
        )
        self.client.force_authenticate(user=self.user)

    def test_create_play(self):
        payload = {
            "title": "Test Title",
            "description": "Test Description",
            "duration": 60,
        }
        res = self.client.post(PLAY_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        play = Play.objects.get(id=res.data["id"])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(play, key))

    def test_create_play_with_actors_and_genres(self):
        actor_1 = sample_actor(first_name="John", last_name="Mitchel")
        actor_2 = sample_actor(first_name="John", last_name="Mitchel")
        genre_1 = sample_genre(name="Drama")
        genre_2 = sample_genre(name="Mystery")
        payload = {
            "title": "Test Title",
            "description": "Test Description",
            "duration": 60,
            "actors": [actor_1.id, actor_2.id],
            "genres": [genre_1.id, genre_2.id],
        }
        res = self.client.post(PLAY_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        play = Play.objects.get(id=res.data["id"])
        self.assertEqual(play.actors.count(), 2)
        self.assertEqual(play.genres.count(), 2)
        self.assertEqual(play.title, payload["title"])
        self.assertEqual(play.description, payload["description"])
        self.assertEqual(play.duration, payload["duration"])


class PlayImageUploadTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_superuser(
            "adminuser", "admin@admin.test", "testpass"
        )
        self.client.force_authenticate(user=self.user)
        self.play = sample_play()
        self.performance = sample_performance(play=self.play)

    def tearDown(self):
        self.play.image.delete()

    def test_upload_image_to_play(self):
        url = image_upload_url(self.play.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"image": ntf}, format="multipart")
        self.play.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.play.image.path))

    def test_upload_image_bad_request(self):
        url = image_upload_url(self.play.id)
        res = self.client.post(url, {"image": "not image"}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_image_to_play_list(self):
        url = PLAY_URL
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            actor = sample_actor(first_name="John", last_name="Mitchel")
            genre = sample_genre(name="Drama")
            res = self.client.post(
                url,
                {
                    "title": "Test",
                    "description": "Description",
                    "actors": [actor.id],
                    "genres": [genre.id],
                    "duration": 60,
                    "image": ntf,
                },
                format="multipart",
            )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        play = Play.objects.get(title="Test")
        self.assertFalse(play.image)

    def test_image_url_is_shown_on_play_detail(self):
        url = image_upload_url(self.play.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(detail_url(self.play.id))
        self.assertIn("image", res.data)

    def test_image_url_is_shown_on_performance_detail(self):
        url = image_upload_url(self.play.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(PLAY_URL)

        self.assertIn("image", res.data[0].keys())
