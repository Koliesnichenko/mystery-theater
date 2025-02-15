from datetime import datetime

from django.db.models import F, Count, Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from theater.models import (
    Genre,
    Actor,
    Play,
    Performance,
    TheaterHall,
    Reservation,
    Ticket,
)
from theater.permissions import IsAdminOrAuthenticatedReadOnly
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
    PlayImageSerializer,
)


class GenreViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [
        IsAdminOrAuthenticatedReadOnly,
    ]


class ActorViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    permission_classes = [
        IsAdminOrAuthenticatedReadOnly,
    ]


class OrderPagination(PageNumberPagination):
    page_size = 5
    max_page_size = 50


class PlayViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Play.objects.prefetch_related("genres", "actors")
    permission_classes = (IsAdminOrAuthenticatedReadOnly,)

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
            filters &= Q(actors__first_name__icontains=actors) | Q(
                actors__last_name__icontains=actors
            )

        return queryset.filter(filters).distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return PlayListSerializer

        if self.action == "retrieve":
            return PlayDetailSerializer

        if self.action == "upload_image":
            return PlayImageSerializer

        return PlaySerializer

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser],
    )
    def upload_image(self, request, pk=None):
        play = self.get_object()
        serializer = self.get_serializer(play, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "genres",
                type=OpenApiTypes.STR,
                description="Filter by genres(ex. ?genres=genre)",
            ),
            OpenApiParameter(
                "actors",
                type=OpenApiTypes.STR,
                description="Filter by actors(ex. ?actors=name)",
            ),
            OpenApiParameter(
                "title",
                type=OpenApiTypes.STR,
                description="Filter by title (ex. ?title=title)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class TicketViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    pagination_class = OrderPagination
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        queryset = Ticket.objects.select_related()
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return TicketListSerializer
        return TicketSerializer


class TheaterHallViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    queryset = TheaterHall.objects.all()
    serializer_class = TheaterHallSerializer
    permission_classes = [
        IsAdminOrAuthenticatedReadOnly,
    ]


class ReservationViewSet(
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Reservation.objects.prefetch_related(
        "tickets__performance__play", "tickets__performance__theater_hall"
    )
    serializer_class = ReservationSerializer
    pagination_class = OrderPagination
    permission_classes = [
        IsAuthenticated,
    ]

    def get_serializer_class(self):
        if self.action == "list":
            return ReservationListSerializer

        return ReservationSerializer

    def get_queryset(self):
        return Reservation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PerformanceViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
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
    permission_classes = [
        IsAdminOrAuthenticatedReadOnly,
    ]

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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "date",
                type=OpenApiTypes.DATE,
                description="Filter by date (format: YYYY-MM-DD)",
            ),
            OpenApiParameter(
                "play",
                type=OpenApiTypes.INT,
                description="Filter by play(ex. ?play=4)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
