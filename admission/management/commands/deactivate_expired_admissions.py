from django.core.management.base import BaseCommand
from admission.models import AdmissionInfo
from django.utils import timezone


class Command(BaseCommand):
    help = 'Muddati tugagan qabul ma\'lumotlarini avtomatik nofaol qiladi'

    def handle(self, *args, **options):
        """Muddati tugagan qabul ma\'lumotlarini nofaol qilish"""
        deactivated_count = AdmissionInfo.deactivate_expired()
        
        if deactivated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'{deactivated_count} ta muddati tugagan qabul ma\'lumoti nofaol qilindi.'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING('Muddati tugagan qabul ma\'lumotlari topilmadi.')
            )
