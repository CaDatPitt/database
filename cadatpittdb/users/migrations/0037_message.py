# Generated by Django 4.1.9 on 2023-07-14 01:31

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0036_remove_dataset_collections"),
    ]

    operations = [
        migrations.CreateModel(
            name="Message",
            fields=[
                (
                    "message_id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="dataset ID",
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        max_length=254, unique=True, verbose_name="email address"
                    ),
                ),
                (
                    "full_name",
                    models.CharField(max_length=150, verbose_name="full name"),
                ),
                (
                    "inquiry_type",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=100,
                        verbose_name="inquiry type",
                    ),
                ),
                (
                    "subject",
                    models.CharField(
                        blank=True, default="", max_length=200, verbose_name="subject"
                    ),
                ),
                (
                    "message",
                    models.CharField(
                        blank=True, default="", max_length=5000, verbose_name="message"
                    ),
                ),
                (
                    "date_submitted",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="date submitted"
                    ),
                ),
            ],
            options={
                "verbose_name": "message",
                "verbose_name_plural": "messages",
            },
        ),
    ]