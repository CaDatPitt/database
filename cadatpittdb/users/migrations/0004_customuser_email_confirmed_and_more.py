# Generated by Django 4.1.9 on 2023-06-22 17:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0003_pinneddataset_date_pinned_pinneditem_date_pinned_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="email_confirmed",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="customuser",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
    ]
