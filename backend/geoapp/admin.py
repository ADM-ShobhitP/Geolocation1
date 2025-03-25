from django.contrib import admin
from .models import User, Plant, Schedule, PlantBoundary, DataCollector

# Register your models here.
class UserAdmin(admin.ModelAdmin):
    list_display=['id','username', 'password', 'role']

admin.site.register(User, UserAdmin)
admin.site.register(Plant)
admin.site.register(Schedule)
admin.site.register(PlantBoundary)
admin.site.register(DataCollector)