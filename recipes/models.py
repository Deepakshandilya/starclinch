from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class Recipe(models.Model):
    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        limit_choices_to={'role': 'seller'},  # DB level hint
    )
    name = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='recipes/images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']  # newest first by default
        indexes = [
            models.Index(fields=['seller']),      # optimized filter by seller
            models.Index(fields=['created_at']),  # optimized ordering
        ]

    def __str__(self):
        return self.name

    def average_rating(self):
        from django.db.models import Avg
        result = self.ratings.aggregate(Avg('score'))
        return round(result['score__avg'] or 0, 2)


class Rating(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ratings',
    )
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ratings',
        limit_choices_to={'role': 'customer'},
    )
    score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # One customer can only rate a recipe once
        unique_together = ['recipe', 'customer']
        indexes = [
            models.Index(fields=['recipe']),
        ]

    def __str__(self):
        return f"{self.customer.username} rated {self.recipe.name} — {self.score}/5"