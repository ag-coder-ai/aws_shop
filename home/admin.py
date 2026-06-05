from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import BrandStory


@admin.register(BrandStory)
class BrandStoryAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "is_active",
        "updated_at"
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "title",
    )