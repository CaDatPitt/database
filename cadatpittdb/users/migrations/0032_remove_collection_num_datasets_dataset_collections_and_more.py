# Generated by Django 4.1.9 on 2023-07-13 21:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0031_remove_collection_has_dataset_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="collection",
            name="num_datasets",
        ),
        migrations.AddField(
            model_name="dataset",
            name="collections",
            field=models.ManyToManyField(to="users.collection"),
        ),
        migrations.AlterField(
            model_name="collection",
            name="sites",
            field=models.CharField(
                blank=True, default="", max_length=100, verbose_name="sites"
            ),
        ),
    ]
