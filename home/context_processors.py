from products.models import Category

def global_data(request):
    return {
        "categories": Category.objects.all()
    }