# Generated by Django 4.1.9 on 2023-07-11 15:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0026_rename_created_by_tag_creator_remove_dataset_editors_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="item",
            name="thumbnail",
            field=models.URLField(
                blank=True, default="", max_length=300, verbose_name="thumbnail"
            ),
        ),
    ]
