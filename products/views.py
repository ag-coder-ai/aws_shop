# products/views.py

from django.db.models import Q
from django.db.models import Min
from django.db.models import Max
from django.db.models import Prefetch

from django.views.generic import ListView

from .models import (
    Product,
    ProductVariant,
    Category,
    Brand,
)


# =========================================================
# INDUSTRY LEVEL PRODUCT LIST VIEW
# =========================================================

class ProductListView(ListView):

    model = Product

    template_name = 'products/product_list.html'

    context_object_name = 'products'

    paginate_by = 12


    # =====================================================
    # MAIN QUERYSET
    # =====================================================

    def get_queryset(self):

        queryset = Product.objects.select_related(
            'category',
            'brand'
        ).prefetch_related(

            Prefetch(
                'variants',
                queryset=ProductVariant.objects.select_related(
                    'size',
                    'color'
                )
            ),

            'images'

        ).filter(

            status='published',
            is_active=True

        ).distinct()


        # =================================================
        # SEARCH
        # =================================================

        search = self.request.GET.get('search')

        if search:

            queryset = queryset.filter(

                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(brand__name__icontains=search) |
                Q(category__name__icontains=search)

            )


        # =================================================
        # CATEGORY FILTER
        # =================================================

        category = self.request.GET.get('category')

        if category:

            queryset = queryset.filter(
                category__slug=category
            )


        # =================================================
        # BRAND FILTER
        # =================================================

        brand = self.request.GET.get('brand')

        if brand:

            queryset = queryset.filter(
                brand__slug=brand
            )


        # =================================================
        # SIZE FILTER
        # =================================================

        size = self.request.GET.get('size')

        if size:

            queryset = queryset.filter(
                variants__size__name=size
            )


        # =================================================
        # COLOR FILTER
        # =================================================

        color = self.request.GET.get('color')

        if color:

            queryset = queryset.filter(
                variants__color__name=color
            )


        # =================================================
        # MIN PRICE FILTER
        # =================================================

        min_price = self.request.GET.get('min_price')

        if min_price:

            queryset = queryset.filter(
                variants__wholesale_price__gte=min_price
            )


        # =================================================
        # MAX PRICE FILTER
        # =================================================

        max_price = self.request.GET.get('max_price')

        if max_price:

            queryset = queryset.filter(
                variants__wholesale_price__lte=max_price
            )


        # =================================================
        # STOCK FILTER
        # =================================================

        in_stock = self.request.GET.get('in_stock')

        if in_stock:

            queryset = queryset.filter(
                variants__stock_quantity__gt=0
            )


        # =================================================
        # FEATURED FILTER
        # =================================================

        featured = self.request.GET.get('featured')

        if featured:

            queryset = queryset.filter(
                is_featured=True
            )


        # =================================================
        # SORTING
        # =================================================

        sort = self.request.GET.get('sort')


        if sort == 'price_low':

            queryset = queryset.annotate(
                min_variant_price=Min(
                    'variants__wholesale_price'
                )
            ).order_by('min_variant_price')


        elif sort == 'price_high':

            queryset = queryset.annotate(
                max_variant_price=Max(
                    'variants__wholesale_price'
                )
            ).order_by('-max_variant_price')


        elif sort == 'oldest':

            queryset = queryset.order_by('created_at')


        elif sort == 'name_az':

            queryset = queryset.order_by('name')


        elif sort == 'name_za':

            queryset = queryset.order_by('-name')


        else:

            queryset = queryset.order_by(
                '-created_at'
            )


        return queryset.distinct()


    # =====================================================
    # EXTRA CONTEXT
    # =====================================================

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context['categories'] = Category.objects.filter(
            is_active=True
        )

        context['brands'] = Brand.objects.filter(
            is_active=True
        )

        context['selected_category'] = self.request.GET.get(
            'category', ''
        )

        context['selected_brand'] = self.request.GET.get(
            'brand', ''
        )

        context['selected_size'] = self.request.GET.get(
            'size', ''
        )

        context['selected_color'] = self.request.GET.get(
            'color', ''
        )

        context['search_query'] = self.request.GET.get(
            'search', ''
        )

        context['sort_option'] = self.request.GET.get(
            'sort', ''
        )

        return context


# products/views.py


from django.shortcuts import get_object_or_404

# products/views.py

from django.views.generic import DetailView
from django.db.models import Prefetch

from .models import (
    Product,
    ProductVariant
)


# =========================================================
# PRODUCT DETAIL VIEW
# INDUSTRY LEVEL
# =========================================================

class ProductDetailView(DetailView):

    model = Product

    template_name = "products/product_detail.html"

    context_object_name = "product"

    slug_field = "slug"

    slug_url_kwarg = "slug"




    # =====================================================
    # OPTIMIZED QUERYSET
    # =====================================================

    def get_queryset(self):

        return Product.objects.select_related(
            "category",
            "brand"
        ).prefetch_related(

            # PRODUCT IMAGES
            "images",

            # ACTIVE VARIANTS ONLY
            Prefetch(
                "variants",
                queryset=ProductVariant.objects.filter(
                    is_active=True
                ).select_related(
                    "size",
                    "color"
                )
            )

        ).filter(
            is_active=True
        )


    # =====================================================
    # CONTEXT DATA
    # =====================================================

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        product = self.object


        # =================================================
        # IMAGES
        # =================================================

        images = list(
            product.images.all()
        )

        context["images"] = images

        context["primary_image"] = next(

            (
                img for img in images
                if img.is_primary
            ),

            images[0] if images else None

        )


        # =================================================
        # VARIANTS
        # =================================================

        variants = list(
            product.variants.all()
        )

        context["variants"] = variants


        # =================================================
        # VARIANT DATA FOR JS
        # =================================================

        context["variant_data"] = [

            {
                "id": variant.id,

                "size": variant.size.name,

                "color": variant.color.name,

                "hex": variant.color.hex_code,

                "price": str(
                    variant.wholesale_price
                ),

                "stock": variant.stock_quantity

            }

            for variant in variants

        ]


        # =================================================
        # UNIQUE SIZES
        # =================================================

        context["sizes"] = sorted(

            set(

                variant.size.name
                for variant in variants

            )

        )


        # =================================================
        # UNIQUE COLORS
        # =================================================

        unique_colors = {}

        for variant in variants:

            color_name = variant.color.name

            if color_name not in unique_colors:

                unique_colors[color_name] = {

                    "name": color_name,

                    "hex_code":
                        variant.color.hex_code

                }

        context["colors"] = unique_colors.values()


        # =================================================
        # DEFAULT PRICE
        # =================================================

        first_variant = variants[0] if variants else None

        context["default_price"] = (

            first_variant.wholesale_price
            if first_variant else 0

        )


        # =================================================
        # TOTAL STOCK
        # =================================================

        context["total_stock"] = sum(

            variant.stock_quantity
            for variant in variants

        )


        # =================================================
        # RELATED PRODUCTS
        # =================================================

        context["related_products"] = Product.objects.select_related(
            "brand",
            "category"
        ).prefetch_related(
            "images",
            "variants"
        ).filter(

            category=product.category,

            is_active=True,

            status="published"

        ).exclude(
            id=product.id
        )[:8]


        return context


