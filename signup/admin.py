from django.contrib import admin
from .models import Concert, Performance, Performer
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
# Register your models here.
class ConcertAdmin(admin.ModelAdmin):
    pass


class PerformanceAdmin(admin.ModelAdmin):
    pass


class PerformerInline(admin.StackedInline):
    model = Performer
    can_delete = False
    verbose_name_plural = "performers"


class UserAdmin(BaseUserAdmin):
    inlines = (PerformerInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Concert, ConcertAdmin)
admin.site.register(Performance, PerformanceAdmin)