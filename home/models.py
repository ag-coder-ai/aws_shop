from django.db import models

# Create your models here.
from django.db import models


class BrandStory(models.Model):
    title = models.CharField(max_length=200)

    subtitle = models.CharField(
        max_length=100,
        default="OUR BRAND"
    )

    description = models.TextField()

    image = models.ImageField(
        upload_to="brand_story/"
    )

    feature_1 = models.CharField(
        max_length=100,
        blank=True
    )

    feature_2 = models.CharField(
        max_length=100,
        blank=True
    )

    feature_3 = models.CharField(
        max_length=100,
        blank=True
    )

    feature_4 = models.CharField(
        max_length=100,
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "Brand Story"
        verbose_name_plural = "Brand Story"

    def __str__(self):
        return self.title