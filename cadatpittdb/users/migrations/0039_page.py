# Generated by Django 4.1.9 on 2023-07-14 13:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0038_alter_message_email"),
    ]

    operations = [
        migrations.CreateModel(
            name="Page",
            fields=[
                (
                    "page_id",
                    models.CharField(
                        max_length=200,
                        primary_key=True,
                        serialize=False,
                        verbose_name="page ID",
                    ),
                ),
                ("title", models.CharField(max_length=200, verbose_name="title")),
                (
                    "url",
                    models.CharField(
                        blank=True, default="", max_length=300, verbose_name="url"
                    ),
                ),
                (
                    "content",
                    models.CharField(
                        blank=True, default="", max_length=8000, verbose_name="content"
                    ),
                ),
            ],
            options={
                "verbose_name": "page",
                "verbose_name_plural": "pages",
            },
        ),
    ]