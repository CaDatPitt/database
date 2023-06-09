# Generated by Django 4.1.9 on 2023-07-03 20:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0006_remove_dataset_items_remove_item_collections_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="pinneddataset",
            old_name="fk_dataset_id",
            new_name="fk_dataset",
        ),
        migrations.RenameField(
            model_name="pinneddataset",
            old_name="fk_user_id",
            new_name="fk_user",
        ),
        migrations.RenameField(
            model_name="pinneditem",
            old_name="fk_dataset_id",
            new_name="fk_dataset",
        ),
        migrations.RenameField(
            model_name="pinneditem",
            old_name="fk_user_id",
            new_name="fk_user",
        ),
    ]
