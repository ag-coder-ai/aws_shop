# products/models.py

import uuid

from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError


# =========================================================
# BASE MODEL
# =========================================================

class BaseModel(models.Model):

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        abstract = True


# =========================================================
# CATEGORY
# =========================================================

class Category(BaseModel):

    name = models.CharField(
        max_length=100,
        unique=True
    )

    slug = models.SlugField(
        unique=True,
        blank=True
    )

    image = models.ImageField(
        upload_to='categories/',
        blank=True,
        null=True
    )

    is_active = models.BooleanField(default=True)

    class Meta:

        verbose_name_plural = "Categories"

        ordering = ['name']

        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
        ]

    def save(self, *args, **kwargs):

        if not self.slug:

            base_slug = slugify(self.name)

            slug = base_slug

            counter = 1

            while Category.objects.filter(slug=slug).exists():

                slug = f"{base_slug}-{counter}"

                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):

        return self.name


# =========================================================
# BRAND
# =========================================================

class Brand(BaseModel):

    name = models.CharField(
        max_length=100,
        unique=True
    )

    slug = models.SlugField(
        unique=True,
        blank=True
    )

    logo = models.ImageField(
        upload_to='brands/',
        blank=True,
        null=True
    )

    is_active = models.BooleanField(default=True)

    class Meta:

        ordering = ['name']

    def save(self, *args, **kwargs):

        if not self.slug:

            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def __str__(self):

        return self.name


# =========================================================
# SIZE
# =========================================================

class Size(BaseModel):

    name = models.CharField(
        max_length=20,
        unique=True
    )

    sort_order = models.PositiveIntegerField(default=0)

    class Meta:

        ordering = ['sort_order']

    def __str__(self):

        return self.name


# =========================================================
# COLOR
# =========================================================

class Color(BaseModel):

    name = models.CharField(
        max_length=50,
        unique=True
    )

    hex_code = models.CharField(
        max_length=10,
        blank=True,
        null=True
    )

    class Meta:

        ordering = ['name']

    def __str__(self):

        return self.name


# =========================================================
# PRODUCT
# =========================================================

class Product(BaseModel):

    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('out_of_stock', 'Out Of Stock'),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products'
    )

    brand = models.ForeignKey(
        Brand,
        on_delete=models.CASCADE,
        related_name='products'
    )

    name = models.CharField(max_length=255)

    slug = models.SlugField(
        unique=True,
        blank=True
    )

    description = models.TextField()

    material = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    minimum_order_quantity = models.PositiveIntegerField(
        default=1
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    is_featured = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)

    meta_title = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    meta_description = models.TextField(
        blank=True,
        null=True
    )

    class Meta:

        ordering = ['-created_at']

        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status']),
            models.Index(fields=['is_active']),
        ]

    def save(self, *args, **kwargs):

        if not self.slug:

            base_slug = slugify(self.name)

            slug = base_slug

            counter = 1

            while Product.objects.filter(slug=slug).exists():

                slug = f"{base_slug}-{counter}"

                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    @property
    def primary_image(self):
        return self.images.filter(is_primary=True).first()

    @property
    def total_stock(self):

        return sum(
            variant.stock_quantity
            for variant in self.variants.all()
        )




# =========================================================
# PRODUCT VARIANT
# =========================================================

class ProductVariant(BaseModel):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants'
    )

    size = models.ForeignKey(
        Size,
        on_delete=models.CASCADE,
        related_name='variants'
    )

    color = models.ForeignKey(
        Color,
        on_delete=models.CASCADE,
        related_name='variants'
    )

    sku = models.CharField(
        max_length=100,
        unique=True
    )

    wholesale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    stock_quantity = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)
    reserved_stock = models.PositiveIntegerField(default=0)

    class Meta:

        unique_together = ['product', 'size', 'color']

        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['stock_quantity']),
        ]

    @property
    def in_stock(self):

        return self.stock_quantity > 0

    def clean(self):

        if self.stock_quantity < 0:

            raise ValidationError(
                "Stock cannot be negative"
            )

    def __str__(self):

        return (
            f"{self.product.name} - "
            f"{self.size.name} - "
            f"{self.color.name}"
        )

    @property
    def available_stock(self):
        return self.stock_quantity - self.reserved_stock


# =========================================================
# PRODUCT IMAGES
# =========================================================

class ProductImage(BaseModel):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )

    image = models.ImageField(
        upload_to='products/'
    )

    is_primary = models.BooleanField(default=False)

    class Meta:

        ordering = ['-is_primary']

    def __str__(self):

        return self.product.name


# =========================================================
# INVENTORY LOG
# =========================================================

class InventoryLog(BaseModel):

    TRANSACTION_TYPES = (
        ('added', 'Added'),
        ('removed', 'Removed'),
        ('order', 'Order'),
        ('return', 'Return'),
    )

    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name='inventory_logs'
    )

    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES
    )

    quantity = models.IntegerField()

    note = models.TextField(
        blank=True,
        null=True
    )

    class Meta:

        ordering = ['-created_at']

    def __str__(self):

        return (
            f"{self.variant.sku} - "
            f"{self.transaction_type}"
        )


