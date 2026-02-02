from django.core.management.base import BaseCommand
from api.ingestion_tasks import ingest_customer_data, ingest_loan_data
import os

class Command(BaseCommand):
    help = 'Trigger background ingestion of Excel files'

    def add_arguments(self, parser):
        parser.add_argument('--customer_file', type=str, default='customer_data.xlsx')
        parser.add_argument('--loan_file', type=str, default='loan_data.xlsx')

    def handle(self, *args, **options):
        customer_file = options['customer_file']
        loan_file = options['loan_file']
        
        # Trigger Celery tasks
        self.stdout.write(f"Triggering ingestion for {customer_file}...")
        ingest_customer_data.delay(customer_file)
        
        self.stdout.write(f"Triggering ingestion for {loan_file}...")
        ingest_loan_data.delay(loan_file)
        
        self.stdout.write(self.style.SUCCESS('Tasks submitted to queue.'))
