from django.db.models.signals import pre_delete
from django.dispatch import receiver
from .models import NotaFiscal


@receiver(pre_delete, sender=NotaFiscal)
def delete_files_on_nota_delete(sender, instance, **kwargs):
    """
    Remove os arquivos do storage (local ou R2) antes da nota ser apagada.
    """
    if instance.pdf_nota:
        instance.pdf_nota.delete(save=False)

    for anexo in instance.anexos.all():
        if anexo.arquivo:
            anexo.arquivo.delete(save=False)
