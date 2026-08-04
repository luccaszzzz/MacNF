from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("notas", "0007_anexonotafiscal"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS notas_anexonotafiscal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                arquivo varchar(100) NOT NULL,
                criado_em datetime NOT NULL,
                nota_id integer NOT NULL REFERENCES notas_notafiscal(id) DEFERRABLE INITIALLY DEFERRED
            );
            """,
            reverse_sql="DROP TABLE IF EXISTS notas_anexonotafiscal;",
            state_operations=[
                migrations.CreateModel(
                    name="AnexoNotaFiscal",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("arquivo", models.FileField(upload_to="notas/anexos/%Y/%m/")),
                        ("criado_em", models.DateTimeField(auto_now_add=True)),
                        (
                            "nota",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="anexos",
                                to="notas.notafiscal",
                            ),
                        ),
                    ],
                    options={"ordering": ["id"]},
                )
            ],
        )
    ]
