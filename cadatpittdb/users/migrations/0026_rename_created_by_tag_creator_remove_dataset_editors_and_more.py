# Generated by Django 4.1.9 on 2023-07-11 14:47

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0025_rename_created_by_dataset_creator_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="tag",
            old_name="created_by",
            new_name="creator",
        ),
        migrations.RemoveField(
            model_name="dataset",
            name="editors",
        ),
        migrations.AddField(
            model_name="dataset",
            name="editors",
            field=models.ManyToManyField(
                related_name="editor", to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
