from .models import Tag


def sidebar_tags(request):
    return {"sidebar_tags": Tag.objects.order_by("pk")[:8]}