from rest_framework import serializers
from .models import Recipe, Rating


class RatingSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.username', read_only=True)

    class Meta:
        model = Rating
        fields = ['id', 'customer_name', 'score', 'review', 'created_at']
        read_only_fields = ['customer_name', 'created_at']


class RecipeSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source='seller.username', read_only=True)
    average_rating = serializers.SerializerMethodField()
    ratings = RatingSerializer(many=True, read_only=True)

    class Meta:
        model = Recipe
        fields = [
            'id', 'name', 'description', 'image',
            'seller_name', 'average_rating', 'ratings',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['seller_name', 'average_rating', 'ratings', 'created_at', 'updated_at']

    def get_average_rating(self, obj):
        return obj.average_rating()


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Separate serializer for create/update — sellers only"""
    class Meta:
        model = Recipe
        fields = ['name', 'description', 'image']