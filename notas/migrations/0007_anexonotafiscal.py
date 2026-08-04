from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("notas", "0006_notafiscal_observacao_resposta_and_more"),
    ]

    operations = [
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
        ),
    ]
