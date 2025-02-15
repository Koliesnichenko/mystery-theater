import os
import uuid

from django.conf import settings
from django.db import models
from django.utils.text import slugify
from rest_framework.exceptions import ValidationError


class TheaterHall(models.Model):
    name = models.CharField(max_length=100)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()

    @property
    def capacity(self) -> int:
        return self.rows * self.seats_in_row

    def __str__(self):
        return self.name


class Actor(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Genre(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


def play_image_file_path(instance, filename):
    _, extension = os.path.splitext(filename)
    filename = f"{slugify(instance.title)}-{uuid.uuid4()}{extension}"

    return os.path.join("uploads/plays/", filename)


class Play(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    duration = models.IntegerField()
    genres = models.ManyToManyField(Genre, blank=True, related_name="plays")
    actors = models.ManyToManyField(Actor, blank=True, related_name="plays")
    image = models.ImageField(null=True, upload_to=play_image_file_path)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return f"{self.title} - {self.description[:50]}..."


class Performance(models.Model):
    play = models.ForeignKey(Play, on_delete=models.CASCADE)
    theater_hall = models.ForeignKey(TheaterHall, on_delete=models.CASCADE)
    show_time = models.DateTimeField()

    class Meta:
        ordering = ["-show_time"]

    def __str__(self):
        return self.play.title + " " + str(self.show_time)


class Reservation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reservations"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return str(self.created_at)


class Ticket(models.Model):
    performance = models.ForeignKey(
        Performance, on_delete=models.CASCADE, related_name="tickets"
    )
    reservation = models.ForeignKey(
        Reservation, on_delete=models.CASCADE, related_name="tickets"
    )
    row = models.IntegerField()
    seat = models.IntegerField()

    @staticmethod
    def validate_ticket(row, seat, theater_hall, error_to_raise=ValidationError):
        errors = {}

        for ticket_attr_value, ticket_attr_name, theater_hall_attr_name in [
            (row, "row", "rows"),
            (seat, "seat", "seats_in_row"),
        ]:
            count_attrs = getattr(theater_hall, theater_hall_attr_name, 0)
            if not (1 <= ticket_attr_value <= count_attrs):
                errors[ticket_attr_name] = (
                    f"{ticket_attr_name.capitalize()} "
                    f"must be in available range "
                    f" (1, {count_attrs}"
                )
        if errors:
            raise error_to_raise(errors)

    def clean(self):
        self.validate_ticket(
            self.row,
            self.seat,
            self.performance.theater_hall,
            ValidationError,
        )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{str(self.performance)} (row: {self.row}, seat: {self.seat})"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["performance", "row", "seat"],
                name="unique_ticket_performance_seat",
            )
        ]
        ordering = ["row", "seat"]
