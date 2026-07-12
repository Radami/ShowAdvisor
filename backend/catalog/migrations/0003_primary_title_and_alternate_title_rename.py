# Written by hand: makemigrations would need interactive confirmation to
# detect these as renames rather than drop-and-recreate.
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0002_tmdbmoviecache_tmdbshowcache_tvmazeshowcache"),
    ]

    operations = [
        migrations.RenameModel(old_name="ShowTitle", new_name="AlternateShowTitle"),
        migrations.RenameModel(old_name="MovieTitle", new_name="AlternateMovieTitle"),
        migrations.RenameField(model_name="show", old_name="title", new_name="primary_title"),
        migrations.RenameField(model_name="movie", old_name="title", new_name="primary_title"),
        migrations.RemoveField(model_name="alternateshowtitle", name="is_primary"),
        migrations.RemoveField(model_name="alternatemovietitle", name="is_primary"),
        migrations.AlterField(
            model_name="alternateshowtitle",
            name="show",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="alternate_titles",
                to="catalog.show",
            ),
        ),
        migrations.AlterField(
            model_name="alternatemovietitle",
            name="movie",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="alternate_titles",
                to="catalog.movie",
            ),
        ),
    ]
