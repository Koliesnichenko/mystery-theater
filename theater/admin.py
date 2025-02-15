from django.contrib import admin

from theater.models import (
    Genre,
    Actor,
    Play,
    Performance,
    Ticket,
    Reservation,
    TheaterHall,
)


class TicketInline(admin.TabularInline):
    model = Ticket
    extra = 1


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    inlines = (TicketInline,)


admin.site.register(Genre)
admin.site.register(Actor)
admin.site.register(Play)
admin.site.register(Ticket)
admin.site.register(Performance)
admin.site.register(TheaterHall)
