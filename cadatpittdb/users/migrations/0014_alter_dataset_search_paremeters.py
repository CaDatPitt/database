# Generated by Django 4.1.9 on 2023-07-05 18:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0013_alter_dataset_search_paremeters"),
    ]

    operations = [
        migrations.AlterField(
            model_name="dataset",
            name="search_paremeters",
            field=models.JSONField(
                blank=True, default=dict, verbose_name="search parameters"
            ),
        ),
    ]