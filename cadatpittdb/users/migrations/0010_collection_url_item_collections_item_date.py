# Generated by Django 4.1.9 on 2023-07-05 03:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0009_item_thumbnail"),
    ]

    operations = [
        migrations.AddField(
            model_name="collection",
            name="url",
            field=models.URLField(blank=True, default="", verbose_name="url"),
        ),
        migrations.AddField(
            model_name="item",
            name="collections",
            field=models.ManyToManyField(to="users.collection"),
        ),
        migrations.AddField(
            model_name="item",
            name="date",
            field=models.CharField(
                blank=True, default="", max_length=50, verbose_name="date"
            ),
        ),
    ]
