# Generated by Django 4.1.9 on 2023-07-04 06:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0008_remove_pinneditem_fk_dataset_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="item",
            name="thumbnail",
            field=models.URLField(blank=True, default="", verbose_name="thumbnail"),
        ),
    ]
