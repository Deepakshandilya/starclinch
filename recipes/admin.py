from django.contrib import admin
from .models import Recipe, Rating


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ['name', 'seller', 'average_rating', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'seller__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['recipe', 'customer', 'score', 'created_at']
    list_filter = ['score']
    search_fields = ['recipe__name', 'customer__username']