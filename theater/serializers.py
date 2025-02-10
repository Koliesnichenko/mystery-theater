from django.db import transaction
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


class PlayListSerializer(PlaySerializer):
    actors = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="full_name"
    )
    genres = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="name"
    )

    class Meta:
        model = Play
        fields = ("id", "title", "description", "actors", "genres")


class PlayDetailSerializer(PlaySerializer):
    actors = ActorSerializer(many=True, read_only=True)
    genres = GenreSerializer(many=True, read_only=True)

    class Mete:
        model = Play
        fields = (
            "id",
            "title",
            "duration",
            "description",
            "actors",
            "genres",
        )


class TheaterHallSerializer(serializers.ModelSerializer):
    class Meta:
        model = TheaterHall
        fields = ("id", "name", "rows", "seats_in_row", "capacity")


class PerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Performance
        fields = ("id", "play", "theater_hall", "show_time")


class PerformanceListSerializer(PerformanceSerializer):
    play_title = serializers.CharField(source="play.title", read_only=True)
    theater_hall = serializers.CharField(
        source="theater_hall.name",
        read_only=True
    )
    theater_hall_capacity = serializers.CharField(
        source="theater_hall.capacity",
        read_only=True
    )

    class Meta:
        model = Performance
        fields = (
            "id",
            "play_title",
            "theater_hall",
            "theater_hall_capacity",
            "show_time"
        )


class PerformanceDetailSerializer(PerformanceSerializer):
    play = PlayListSerializer(read_only=True)
    theater_hall = TheaterHallSerializer(read_only=True)

    class Meta:
        model = Performance
        fields = (
            "id",
            "play",
            "theater_hall",
            "show_time"
        )


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


class TicketListSerializer(TicketSerializer):
    performance = PerformanceListSerializer(many=False, read_only=True)


class ReservationSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Reservation
        fields = ("id", "tickets", "created_at", "user")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            reservation = Reservation.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(reservation=reservation, **ticket_data)
            return reservation


class ReservationListSerializer(ReservationSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)

