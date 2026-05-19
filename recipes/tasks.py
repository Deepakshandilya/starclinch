from celery import shared_task
from PIL import Image
from datetime import datetime
from django.core.mail import send_mail
from django.conf import settings
from .models import Recipe
import boto3
import csv
import os
import io


@shared_task
def compress_recipe_image(image_path):
    """Compress uploaded recipe image to reduce file size."""
    full_path = os.path.join('media', image_path)

    if not os.path.exists(full_path):
        return f"File not found: {full_path}"

    img = Image.open(full_path)

    # Convert RGBA to RGB if needed (JPEG doesn't support transparency)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    # Save with compression (quality=60 reduces size significantly)
    img.save(full_path, optimize=True, quality=60)

    return f"Compressed: {image_path}"

@shared_task
def send_daily_email():
    """Send daily notification email — skips weekends via crontab schedule."""

    latest_recipes = Recipe.objects.order_by('-created_at')[:5]
    recipe_names = "\n".join(recipe.name for recipe in latest_recipes)
    message = f"""Today's latest recipes:

    {recipe_names}

    Visit StarClinch to explore more recipes.
    """

    send_mail(
        subject='StarClinch — Daily Recipe Update',
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[settings.EMAIL_HOST_USER], 
        fail_silently=False,
    )
    return "Daily email sent"

@shared_task
def export_users_to_s3():
    """Fetch all users from DB, export as CSV, upload to S3."""
    from django.contrib.auth import get_user_model
    User = get_user_model()

    users = User.objects.values('id', 'username', 'email', 'role', 'date_joined').iterator(chunk_size=500)

    # Build CSV in memory — no temp file on disk
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=['id', 'username', 'email', 'role', 'date_joined'])
    writer.writeheader()
    writer.writerows(users)

    # Upload to S3
    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )

    filename = f"exports/users_{datetime.now().strftime('%Y_%m_%d')}.csv"

    s3.put_object(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=filename,
        Body=buffer.getvalue(),
        ContentType='text/csv',
    )

    return "Users exported to S3"