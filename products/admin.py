# products/admin.py

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Category,
    Brand,
    Size,
    Color,
    Product,
    ProductVariant,
    ProductImage,
    InventoryLog,
)


# =========================================================
# CATEGORY ADMIN
# =========================================================

@admin.register(Category)

class CategoryAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'name',
        'slug',
        'is_active',
        'created_at',
    )

    list_filter = (
        'is_active',
        'created_at',
    )

    search_fields = (
        'name',
        'slug',
    )

    prepopulated_fields = {
        'slug': ('name',)
    }

    ordering = ('name',)

    list_editable = ('is_active',)

    readonly_fields = (
        'created_at',
        'updated_at',
    )


# =========================================================
# BRAND ADMIN
# =========================================================

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'logo_preview',
        'name',
        'slug',
        'is_active',
        'created_at',
    )

    list_filter = (
        'is_active',
        'created_at',
    )

    search_fields = (
        'name',
        'slug',
    )

    prepopulated_fields = {
        'slug': ('name',)
    }

    ordering = ('name',)

    list_editable = ('is_active',)

    readonly_fields = (
        'logo_preview',
        'created_at',
        'updated_at',
    )

    fieldsets = (

        ('Brand Information', {
            'fields': (
                'name',
                'slug',
                'logo',
                'logo_preview',
                'is_active',
            )
        }),

        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )

    def logo_preview(self, obj):

        if obj.logo:

            return format_html(
                '<img src="{}" width="60" '
                'height="60" style="border-radius:8px;" />',
                obj.logo.url
            )

        return "No Image"

    logo_preview.short_description = "Logo"


# =========================================================
# SIZE ADMIN
# =========================================================

@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'name',
        'sort_order',
    )

    ordering = ('sort_order',)

    search_fields = ('name',)


# =========================================================
# COLOR ADMIN
# =========================================================

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'color_preview',
        'name',
        'hex_code',
    )

    search_fields = ('name',)

    def color_preview(self, obj):

        if obj.hex_code:

            return format_html(
                '<div style="width:30px; '
                'height:30px; '
                'border-radius:50%; '
                'background:{}; '
                'border:1px solid #ccc;"></div>',
                obj.hex_code
            )

        return "-"

    color_preview.short_description = "Preview"


# =========================================================
# PRODUCT IMAGE INLINE
# =========================================================

class ProductImageInline(admin.TabularInline):

    model = ProductImage

    extra = 1

    fields = (
        'image',
        'preview',
        'is_primary',
    )

    readonly_fields = ('preview',)

    def preview(self, obj):

        if obj.image:

            return format_html(
                '<img src="{}" width="70" '
                'height="70" style="border-radius:10px;" />',
                obj.image.url
            )

        return "No Image"

    preview.short_description = "Preview"


# =========================================================
# PRODUCT VARIANT INLINE
# =========================================================

class ProductVariantInline(admin.TabularInline):

    model = ProductVariant

    extra = 1

    autocomplete_fields = (
        'size',
        'color',
    )

    fields = (
        'size',
        'color',
        'sku',
        'wholesale_price',
        'stock_quantity',
        'is_active',
    )



# =========================================================
# PRODUCT ADMIN
# =========================================================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        'product_image',
        'name',
        'brand',
        'category',
        'status',
        'total_stock',
        'is_featured',
        'is_active',
        'created_at',
    )

    list_filter = (
        'status',
        'is_active',
        'is_featured',
        'category',
        'brand',
        'created_at',
    )

    search_fields = (
        'name',
        'description',
        'brand__name',
        'category__name',
    )

    autocomplete_fields = (
        'category',
        'brand',
    )

    readonly_fields = (
        'product_preview',
        'created_at',
        'updated_at',
    )

    list_editable = (
        'status',
        'is_featured',
        'is_active',
    )

    inlines = [
        ProductImageInline,
        ProductVariantInline,
    ]

    fieldsets = (

        ('Basic Information', {
            'fields': (
                'name',
                'category',
                'brand',
                'description',
                'material',
            )
        }),

        ('Product Status', {
            'fields': (
                'status',
                'is_active',
                'is_featured',
            )
        }),

        ('Order Settings', {
            'fields': (
                'minimum_order_quantity',
            )
        }),

        ('SEO Information', {
            'classes': ('collapse',),
            'fields': (
                'meta_title',
                'meta_description',
            )
        }),

        ('Preview', {
            'fields': (
                'product_preview',
            )
        }),

        ('Timestamps', {
            'classes': ('collapse',),
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )

    def product_image(self, obj):

        image = obj.images.filter(
            is_primary=True
        ).first()

        if image:

            return format_html(
                '<img src="{}" width="60" '
                'height="60" '
                'style="border-radius:8px; object-fit:cover;" />',
                image.image.url
            )

        return "No Image"

    product_image.short_description = "Image"

    def product_preview(self, obj):

        image = obj.images.filter(
            is_primary=True
        ).first()

        if image:

            return format_html(
                '<img src="{}" width="250" '
                'style="border-radius:15px;" />',
                image.image.url
            )

        return "No Preview"

    product_preview.short_description = "Preview"

    def total_stock(self, obj):

        return sum(
            variant.stock_quantity
            for variant in obj.variants.all()
        )

    total_stock.short_description = "Total Stock"

# =========================================================
# PRODUCT VARIANT ADMIN
# =========================================================

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):

    list_display = (
        'product',
        'size',
        'color',
        'sku',
        'wholesale_price',
        'stock_quantity',
        'stock_status',
        'is_active',
    )

    list_filter = (
        'is_active',
        'size',
        'color',
    )

    search_fields = (
        'product__name',
        'sku',
    )

    autocomplete_fields = (
        'product',
        'size',
        'color',
    )

    list_editable = (
        'wholesale_price',
        'stock_quantity',
        'is_active',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )

    def stock_status(self, obj):

        if obj.stock_quantity == 0:

            return format_html(
                '<span style="color:red; '
                'font-weight:bold;">Out Of Stock</span>'
            )

        elif obj.stock_quantity < 5:

            return format_html(
                '<span style="color:orange; '
                'font-weight:bold;">Low Stock</span>'
            )

        return format_html(
            '<span style="color:green; '
            'font-weight:bold;">In Stock</span>'
        )

    stock_status.short_description = "Stock Status"


# =========================================================
# PRODUCT IMAGE ADMIN
# =========================================================

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):

    list_display = (
        'product',
        'preview',
        'is_primary',
        'created_at',
    )

    list_filter = (
        'is_primary',
    )

    autocomplete_fields = (
        'product',
    )

    readonly_fields = (
        'preview',
        'created_at',
        'updated_at',
    )

    def preview(self, obj):

        if obj.image:

            return format_html(
                '<img src="{}" width="70" '
                'height="70" style="border-radius:10px;" />',
                obj.image.url
            )

        return "No Image"

    preview.short_description = "Preview"


# =========================================================
# INVENTORY LOG ADMIN
# =========================================================

@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):

    list_display = (
        'variant',
        'transaction_type',
        'quantity',
        'created_at',
    )

    list_filter = (
        'transaction_type',
        'created_at',
    )

    search_fields = (
        'variant__sku',
        'variant__product__name',
    )

    autocomplete_fields = (
        'variant',
    )

    readonly_fields = (
        'variant',
        'transaction_type',
        'quantity',
        'note',
        'created_at',
        'updated_at',
    )

    def has_add_permission(self, request):

        return False

    def has_delete_permission(self, request, obj=None):

        return False