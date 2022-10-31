from django.contrib import admin
from iris_wc.models import CategoryMap, Line, Order, ProductMap


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    pass


@admin.register(Line)
class LineAdmin(admin.ModelAdmin):
    pass


@admin.register(ProductMap)
class ProductMapAdmin(admin.ModelAdmin):
    pass


@admin.register(CategoryMap)
class CategoryMapAdmin(admin.ModelAdmin):
    pass
