from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('cotizador', '0028_add_tag_to_kit_and_kitproducto'),
    ]

    operations = [
        migrations.RunSQL(
            """ALTER TABLE cotizador_kit ADD COLUMN IF NOT EXISTS tag VARCHAR(100) NULL;""",
            """ALTER TABLE cotizador_kit DROP COLUMN IF EXISTS tag;"""
        ),
        migrations.RunSQL(
            """ALTER TABLE cotizador_kitproducto ADD COLUMN IF NOT EXISTS tag VARCHAR(100) NULL;""",
            """ALTER TABLE cotizador_kitproducto DROP COLUMN IF EXISTS tag;"""
        ),
    ]
