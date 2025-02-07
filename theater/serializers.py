from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from theater.models import (
    Genre,
    Actor,
    TheaterHall,
    Performance,
    Play,
    Reservation,
    Ticket,
)


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name")


class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ("id", "first_name", "last_name", "full_name")


class PerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Performance
        fields = ("id", "play", "theatre_hall", "show_time")


class TicketSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        Ticket.validate_ticket(
            attrs["row"],
            attrs["seat"],
            attrs["performance"].theater_hall,
            ValidationError
        )
        return attrs

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "performance", "reservation")


class TheaterHallSerializer(serializers.ModelSerializer):
    class Meta:
        model = TheaterHall
        fields = ("id", "name", "rows", "seats_in_row", "capacity")


class PlaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Play
        fields = (
            "id",
            "title",
            "description",
            "duration",
            "actors",
            "genres",
        )


class ReservationSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)
