import pandas as pd
from celery import shared_task
from .models import Customer, Loan
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@shared_task
def ingest_customer_data(file_path):
    try:
        df = pd.read_excel(file_path)
        # Expected columns: 'Customer ID', 'First Name', 'Last Name', 'Phone Number', 'Monthly Salary', 'Approved Limit'
        # Adjust column names if strictly necessary based on actual file provided (assuming standard case from prompt)
        
        count = 0
        for index, row in df.iterrows():
            try:
                Customer.objects.update_or_create(
                    customer_id=row['Customer ID'],
                    defaults={
                        'first_name': row['First Name'],
                        'last_name': row['Last Name'],
                        'phone_number': str(row['Phone Number']),
                        'monthly_salary': row['Monthly Salary'],
                        'approved_limit': row['Approved Limit'],
                        'current_debt': 0  # Initialize, will be calculated from loans if needed
                    }
                )
                count += 1
            except Exception as e:
                logger.error(f"Error ingesting customer row {index}: {e}")
        
        return f"Successfully ingested {count} customers."
    except Exception as e:
        logger.error(f"Failed to read customer file: {e}")
        return f"Failed: {e}"

@shared_task
def ingest_loan_data(file_path):
    try:
        df = pd.read_excel(file_path)
        # Expected columns: 'Customer ID', 'Loan ID', 'Loan Amount', 'Tenure', 'Interest Rate', 'Monthly repayment', 'EMIs paid on Time', 'Date of Approval', 'End Date'
        
        count = 0
        for index, row in df.iterrows():
            try:
                # Find customer
                customer_id = row['Customer ID']
                try:
                    customer = Customer.objects.get(customer_id=customer_id)
                except Customer.DoesNotExist:
                    logger.error(f"Customer {customer_id} not found for loan {row.get('Loan ID')}")
                    continue

                Loan.objects.update_or_create(
                    loan_id=row['Loan ID'],
                    defaults={
                        'customer': customer,
                        'loan_amount': row['Loan Amount'],
                        'tenure': row['Tenure'],
                        'interest_rate': row['Interest Rate'],
                        'monthly_repayment': row['Monthly repayment'],
                        'emis_paid_on_time': row['EMIs paid on Time'],
                        'start_date': row['Date of Approval'],
                        'end_date': row['End Date']
                    }
                )
                
                # Update customer's current debt
                customer.current_debt += row['Loan Amount']
                customer.save()
                
                count += 1
            except Exception as e:
                logger.error(f"Error ingesting loan row {index}: {e}")
                
        return f"Successfully ingested {count} loans."
    except Exception as e:
        logger.error(f"Failed to read loan file: {e}")
        return f"Failed: {e}"
