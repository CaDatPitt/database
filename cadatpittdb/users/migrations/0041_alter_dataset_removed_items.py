# Generated by Django 4.1.9 on 2023-07-15 02:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0040_alter_dataset_removed_items"),
    ]

    operations = [
        migrations.AlterField(
            model_name="dataset",
            name="removed_items",
            field=models.ManyToManyField(related_name="removed_items", to="users.item"),
        ),
    ]
