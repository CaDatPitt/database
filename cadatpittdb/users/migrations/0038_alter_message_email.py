# Generated by Django 4.1.9 on 2023-07-14 01:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0037_message"),
    ]

    operations = [
        migrations.AlterField(
            model_name="message",
            name="email",
            field=models.EmailField(max_length=254, verbose_name="email address"),
        ),
    ]
