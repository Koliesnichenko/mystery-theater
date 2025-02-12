# Generated by Django 5.2a1 on 2025-02-12 13:28

import theater.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("theater", "0004_alter_actor_first_name_alter_actor_last_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="play",
            name="image",
            field=models.ImageField(
                null=True, upload_to=theater.models.play_image_file_path
            ),
        ),
    ]
