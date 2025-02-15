from django.urls import path, include
from rest_framework import routers

from theater.views import (
    GenreViewSet,
    ActorViewSet,
    PlayViewSet,
    PerformanceViewSet,
    TicketViewSet,
    TheaterHallViewSet,
    ReservationViewSet,
)

router = routers.DefaultRouter()
router.register("genres", GenreViewSet)
router.register("actors", ActorViewSet)
router.register("plays", PlayViewSet)
router.register("performances", PerformanceViewSet)
router.register("tickets", TicketViewSet)
router.register("theater_halls", TheaterHallViewSet)
router.register("reservations", ReservationViewSet)

urlpatterns = [path("", include(router.urls))]

app_name = "theater"
