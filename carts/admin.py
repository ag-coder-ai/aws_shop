# carts/admin.py

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Cart,
    CartItem
)


# =========================================================
# CART ITEM INLINE
# =========================================================

class CartItemInline(admin.TabularInline):

    model = CartItem

    extra = 0

    autocomplete_fields = (
        'variant',
    )

    readonly_fields = (
        'product_image',
        'product_name',
        'variant_info',
        'item_total',
        'created_at',
    )

    fields = (
        'product_image',
        'product_name',
        'variant_info',
        'quantity',
        'item_total',
        'created_at',
    )

    can_delete = True


    # =====================================================
    # PRODUCT IMAGE
    # =====================================================

    def product_image(self, obj):

        image = obj.variant.product.images.filter(
            is_primary=True
        ).first()

        if image:

            return format_html(
                '<img src="{}" width="60" '
                'height="60" '
                'style="border-radius:10px;" />',
                image.image.url
            )

        return "No Image"

    product_image.short_description = "Image"


    # =====================================================
    # PRODUCT NAME
    # =====================================================

    def product_name(self, obj):

        return obj.variant.product.name

    product_name.short_description = "Product"


    # =====================================================
    # VARIANT INFO
    # =====================================================

    def variant_info(self, obj):

        return format_html(

            "<b>Size:</b> {} <br>"
            "<b>Color:</b> {}",

            obj.variant.size.name,
            obj.variant.color.name

        )

    variant_info.short_description = "Variant"


    # =====================================================
    # ITEM TOTAL
    # =====================================================

    def item_total(self, obj):

        total = (
            obj.variant.wholesale_price *
            obj.quantity
        )

        return f"₹{total}"

    item_total.short_description = "Total"


# =========================================================
# CART ADMIN
# =========================================================

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'user',
        'total_items',
        'cart_total',
        'created_at',
        'updated_at',
    )

    search_fields = (
        'user__email',
        'user__username',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'cart_total',
        'total_items',
    )

    inlines = [
        CartItemInline
    ]

    ordering = (
        '-created_at',
    )


    # =====================================================
    # TOTAL ITEMS
    # =====================================================

    def total_items(self, obj):

        return sum(
            item.quantity
            for item in obj.items.all()
        )

    total_items.short_description = "Items"


    # =====================================================
    # CART TOTAL
    # =====================================================

    def cart_total(self, obj):

        total = sum(

            item.variant.wholesale_price *
            item.quantity

            for item in obj.items.all()

        )

        return f"₹{total}"

    cart_total.short_description = "Cart Total"


# =========================================================
# CART ITEM ADMIN
# =========================================================

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):

    list_display = (
        'product_image',
        'cart',
        'product',
        'variant',
        'quantity',
        'price',
        'total_price',
        'created_at',
    )

    list_filter = (
        'created_at',
    )

    search_fields = (
        'variant__product__name',
        'cart__user__email',
        'variant__sku',
    )

    autocomplete_fields = (
        'cart',
        'variant',
    )

    readonly_fields = (
        'product_image',
        'product',
        'price',
        'total_price',
        'created_at',
    )

    ordering = (
        '-created_at',
    )


    # =====================================================
    # PRODUCT IMAGE
    # =====================================================

    def product_image(self, obj):

        image = obj.variant.product.images.filter(
            is_primary=True
        ).first()

        if image:

            return format_html(
                '<img src="{}" width="60" '
                'height="60" '
                'style="border-radius:10px;" />',
                image.image.url
            )

        return "No Image"

    product_image.short_description = "Image"


    # =====================================================
    # PRODUCT
    # =====================================================

    def product(self, obj):

        return obj.variant.product.name

    product.short_description = "Product"


    # =====================================================
    # PRICE
    # =====================================================

    def price(self, obj):

        return f"₹{obj.variant.wholesale_price}"

    price.short_description = "Price"


    # =====================================================
    # TOTAL PRICE
    # =====================================================

    def total_price(self, obj):

        total = (
            obj.variant.wholesale_price *
            obj.quantity
        )

        return f"₹{total}"

    total_price.short_description = "Total"