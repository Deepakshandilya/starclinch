from django.urls import path
from .views import RecipeListCreateView, RecipeDetailView, RatingView

urlpatterns = [
    path('', RecipeListCreateView.as_view(), name='recipe-list'),
    path('<int:pk>/', RecipeDetailView.as_view(), name='recipe-detail'),
    path('<int:pk>/rate/', RatingView.as_view(), name='recipe-rate'),
]