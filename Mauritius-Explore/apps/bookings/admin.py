from django.contrib import admin

from .models import Booking, Payment


class PaymentInline(admin.StackedInline):
    model = Payment
    extra = 0


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('reference', 'event', 'user', 'number_of_people', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'event')
    search_fields = ('reference', 'full_name', 'email', 'user__username')
    readonly_fields = ('reference', 'total_price', 'created_at')
    inlines = [PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('booking', 'method', 'amount', 'status', 'paid_at')
    list_filter = ('status', 'method')
