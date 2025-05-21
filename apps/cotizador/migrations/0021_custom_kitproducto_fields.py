from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('cotizador', '0020_cotizacion_usuario_aprobacion_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            """
            -- Verificar si la columna reference_mask existe y renombrarla a clave
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name = 'cotizador_kitproducto' AND column_name = 'reference_mask') THEN
                    ALTER TABLE cotizador_kitproducto RENAME COLUMN reference_mask TO clave;
                END IF;
                
                -- Si clave no existe pero reference_mask tampoco, crear la columna clave
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'cotizador_kitproducto' AND column_name = 'clave') AND
                   NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'cotizador_kitproducto' AND column_name = 'reference_mask') THEN
                    ALTER TABLE cotizador_kitproducto ADD COLUMN clave VARCHAR(255);
                END IF;
            END
            $$;
            
            -- Añadir nuevos campos a la tabla KitProducto si no existen
            ALTER TABLE cotizador_kitproducto 
            ADD COLUMN IF NOT EXISTS descripcion VARCHAR(255) NULL,
            ADD COLUMN IF NOT EXISTS linea VARCHAR(100) NULL,
            ADD COLUMN IF NOT EXISTS familia VARCHAR(100) NULL,
            ADD COLUMN IF NOT EXISTS grupo VARCHAR(100) NULL,
            ADD COLUMN IF NOT EXISTS mostrar_en_kit BOOLEAN DEFAULT TRUE,
            ADD COLUMN IF NOT EXISTS es_opcional BOOLEAN DEFAULT FALSE;
            
            -- Actualizar la restricción unique_together
            ALTER TABLE cotizador_kitproducto DROP CONSTRAINT IF EXISTS cotizador_kitproducto_kit_id_reference_mask_uniq;
            
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint 
                    WHERE conname = 'cotizador_kitproducto_kit_id_clave_uniq'
                ) THEN
                    ALTER TABLE cotizador_kitproducto ADD CONSTRAINT cotizador_kitproducto_kit_id_clave_uniq UNIQUE (kit_id, clave);
                END IF;
            END
            $$;
            """,
            """
            -- Revertir cambios (renombrar y eliminar columnas)
            ALTER TABLE cotizador_kitproducto DROP CONSTRAINT IF EXISTS cotizador_kitproducto_kit_id_clave_uniq;
            ALTER TABLE cotizador_kitproducto ADD CONSTRAINT cotizador_kitproducto_kit_id_reference_mask_uniq UNIQUE (kit_id, reference_mask);
            
            ALTER TABLE cotizador_kitproducto 
            DROP COLUMN IF EXISTS descripcion,
            DROP COLUMN IF EXISTS linea,
            DROP COLUMN IF EXISTS familia,
            DROP COLUMN IF EXISTS grupo,
            DROP COLUMN IF EXISTS mostrar_en_kit,
            DROP COLUMN IF EXISTS es_opcional;
            
            ALTER TABLE cotizador_kitproducto RENAME COLUMN clave TO reference_mask;
            """
        ),
    ]
