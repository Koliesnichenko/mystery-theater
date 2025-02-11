from datetime import datetime

from django.db.models import F, Count, Q
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from theater.models import (
    Genre,
    Actor,
    Play,
    Performance,
    TheaterHall,
    Reservation,
    Ticket,
)
from theater.serializers import (
    GenreSerializer,
    ActorSerializer,
    TicketSerializer,
    PlaySerializer,
    PerformanceSerializer,
    ReservationSerializer,
    TheaterHallSerializer,
    PlayListSerializer,
    PlayDetailSerializer,
    PerformanceListSerializer,
    PerformanceDetailSerializer,
    ReservationListSerializer,
    TicketListSerializer,
)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class OrderPagination(PageNumberPagination):
    page_size = 5
    max_page_size = 50


class PlayViewSet(viewsets.ModelViewSet):
    queryset = Play.objects.prefetch_related("genres", "actors")

    def get_queryset(self):
        title = self.request.query_params.get("title")
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")

        queryset = self.queryset

        filters = Q()

        if title:
            filters &= Q(title__icontains=title)

        if genres:
            filters &= Q(genres__name__icontains=genres)

        if actors:
            filters &= (Q(actors__first_name__icontains=actors) | Q(actors__last_name__icontains=actors))

        return queryset.filter(filters).distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return PlayListSerializer

        if self.action == "retrieve":
            return PlayDetailSerializer

        return PlaySerializer


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = Ticket.objects.select_related()
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return TicketListSerializer
        return TicketSerializer


class TheaterHallViewSet(viewsets.ModelViewSet):
    queryset = TheaterHall.objects.all()
    serializer_class = TheaterHallSerializer


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.prefetch_related(
        "tickets__performance__play",
        "tickets__performance__theater_hall"
    )
    serializer_class = ReservationSerializer
    pagination_class = OrderPagination

    def get_serializer_class(self):
        if self.action == "list":
            return ReservationListSerializer

        return ReservationSerializer

    def get_queryset(self):
        return Reservation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PerformanceViewSet(viewsets.ModelViewSet):
    queryset = (
        Performance.objects.all()
        .select_related("play", "theater_hall")
        .annotate(
            tickets_available=(
                F("theater_hall__rows") * F("theater_hall__seats_in_row")
                - Count("tickets")
            )
        )
    )
    serializer_class = PerformanceSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        date_str = self.request.query_params.get("date")
        play = self.request.query_params.get("play")

        queryset = self.queryset

        if date_str:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
                queryset = queryset.filter(show_time__date=date)
            except ValueError:
                pass

        if play:
            queryset = queryset.filter(play__id=play)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return PerformanceListSerializer

        if self.action == "retrieve":
            return PerformanceDetailSerializer

        return PerformanceSerializer

