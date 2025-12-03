from django.views.generic import ListView, TemplateView

from .models import MenuCategory, MenuItem


class HomeView(TemplateView):
    """Landing page where customers will browse a preview of the menu."""

    template_name = 'orders/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categories = MenuCategory.objects.all()
        items = MenuItem.objects.filter(is_available=True)[:6]

        context["categories"] = categories
        context["menu_items"] = items
        context["selected_category"] = None
        context["selected_tag"] = None
        return context


class MenuListView(ListView):
    """Full menu page with filters by category/tag."""

    model = MenuItem
    template_name = 'orders/menu_list.html'
    context_object_name = 'menu_items'

    def get_queryset(self):
        qs = MenuItem.objects.filter(is_available=True)
        self.selected_category = self.request.GET.get("category") or ""
        self.selected_tag = self.request.GET.get("tag") or ""

        if self.selected_category:
            qs = qs.filter(category__slug=self.selected_category)
        if self.selected_tag in {choice[0] for choice in MenuItem.Tags.choices}:
            qs = qs.filter(tag=self.selected_tag)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = MenuCategory.objects.all()
        context["selected_category"] = self.selected_category
        context["selected_tag"] = self.selected_tag
        return context
