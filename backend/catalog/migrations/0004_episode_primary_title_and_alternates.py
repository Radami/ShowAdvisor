# Written by hand: the rename needs interactive confirmation makemigrations
# can't get in this environment.
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0003_primary_title_and_alternate_title_rename"),
    ]

    operations = [
        migrations.RenameField(
            model_name="episode", old_name="title", new_name="primary_title"
        ),
        migrations.CreateModel(
            name="AlternateEpisodeTitle",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(db_index=True, max_length=500)),
                ("language", models.CharField(blank=True, max_length=10)),
                ("country", models.CharField(blank=True, max_length=2)),
                (
                    "episode",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="alternate_titles",
                        to="catalog.episode",
                    ),
                ),
            ],
        ),
    ]
