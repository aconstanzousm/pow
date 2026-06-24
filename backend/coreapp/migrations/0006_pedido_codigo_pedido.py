from django.db import migrations, models
import secrets


def _generate_codigo():
    return f"PED-{secrets.token_hex(3).upper()}"


def populate_codigos(apps, schema_editor):
    Pedido = apps.get_model("coreapp", "Pedido")
    used_codes = set(
        Pedido.objects.exclude(codigo_pedido__isnull=True).exclude(codigo_pedido="").values_list("codigo_pedido", flat=True)
    )

    for pedido in Pedido.objects.filter(models.Q(codigo_pedido__isnull=True) | models.Q(codigo_pedido="")):
        codigo = _generate_codigo()
        while codigo in used_codes:
            codigo = _generate_codigo()
        pedido.codigo_pedido = codigo
        pedido.save(update_fields=["codigo_pedido"])
        used_codes.add(codigo)


class Migration(migrations.Migration):

    dependencies = [
        ("coreapp", "0005_producto_stock_minimo_alter_producto_stock"),
    ]

    operations = [
        migrations.AddField(
            model_name="pedido",
            name="codigo_pedido",
            field=models.CharField(blank=True, db_index=True, editable=False, max_length=10, null=True),
        ),
        migrations.RunPython(populate_codigos, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="pedido",
            name="codigo_pedido",
            field=models.CharField(db_index=True, editable=False, max_length=10, unique=True),
        ),
    ]
