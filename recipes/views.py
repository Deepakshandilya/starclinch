from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import Recipe, Rating
from .serializers import RecipeSerializer, RecipeWriteSerializer, RatingSerializer
from users.permissions import IsSeller, IsCustomer


class RecipeListCreateView(APIView):

    def get_permissions(self):
        # Anyone can view recipes, only sellers can create
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsSeller()]

    def get(self, request):
        recipes = Recipe.objects.select_related('seller').prefetch_related('ratings').all()
        serializer = RecipeSerializer(recipes, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = RecipeWriteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(seller=request.user)  # attach logged in seller
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RecipeDetailView(APIView):

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsSeller()]

    def get_object(self, pk):
        try:
            return Recipe.objects.select_related('seller').prefetch_related('ratings').get(pk=pk)
        except Recipe.DoesNotExist:
            return None

    def get(self, request, pk):
        recipe = self.get_object(pk)
        if not recipe:
            return Response({'error': 'Recipe not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = RecipeSerializer(recipe)
        return Response(serializer.data)

    def patch(self, request, pk):
        recipe = self.get_object(pk)
        if not recipe:
            return Response({'error': 'Recipe not found'}, status=status.HTTP_404_NOT_FOUND)
        # Seller can only edit their own recipe
        if recipe.seller != request.user:
            return Response({'error': 'Not your recipe'}, status=status.HTTP_403_FORBIDDEN)
        serializer = RecipeWriteSerializer(recipe, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        recipe = self.get_object(pk)
        if not recipe:
            return Response({'error': 'Recipe not found'}, status=status.HTTP_404_NOT_FOUND)
        if recipe.seller != request.user:
            return Response({'error': 'Not your recipe'}, status=status.HTTP_403_FORBIDDEN)
        recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RatingView(APIView):
    permission_classes = [IsCustomer]  # only customers can rate

    def post(self, request, pk):
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response({'error': 'Recipe not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if already rated
        if Rating.objects.filter(recipe=recipe, customer=request.user).exists():
            return Response({'error': 'You have already rated this recipe'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = RatingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(recipe=recipe, customer=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)