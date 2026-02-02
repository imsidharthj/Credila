# Alemeno Credit Approval System
Backend Assignment by [Your Name]

## Overview
A Django-based Credit Approval System that calculates creditworthiness, processes loans, and manages customer data. It uses Celery/Redis for background ingestion of historical data.

## Tech Stack
- **Framework**: Django 4.2 + Django Rest Framework
- **Database**: PostgreSQL 13
- **Async Workers**: Celery + Redis
- **Containerization**: Docker Compose

## Setup Instructions

### Prerequisites
- Docker & Docker Compose

### Running the App
1. Clone the repository.
2. Run the application:
   ```bash
   docker-compose up -d --build
   ```
3. The API will be available at `http://localhost:8000/`.

### Ingesting Data
To ingest `customer_data.xlsx` and `loan_data.xlsx`:
1. Ensure the files are in the root directory (or mapped volume).
2. Run the management command:
   ```bash
   docker-compose run web python manage.py trigger_ingestion --customer_file customer_data.xlsx --loan_file loan_data.xlsx
   ```

## API Endpoints

### 1. Register Customer
**POST** `/api/register`
- Inputs: `first_name`, `last_name`, `age`, `monthly_income`, `phone_number`.
- Calculates `approved_limit`.

### 2. Check Eligibility
**POST** `/api/check-eligibility`
- Inputs: `customer_id`, `loan_amount`, `interest_rate`, `tenure`.
- Returns: Approval status and corrected interest rate.

### 3. Create Loan
**POST** `/api/create-loan`
- Inputs: same as check-eligibility.
- Creates loan if eligible.

### 4. View Loan
**GET** `/api/view-loan/{loan_id}`

### 5. View Customer Loans
**GET** `/api/view-loans/{customer_id}`

## Credit Score Logic
The determination of the credit score is based on:
1. **Past on-time payments**: +0.5 points per EMI.
2. **Total Loans**: +5 points per loan.
3. **Current Year Activity**: -10 points per new loan this year.
4. **Approved Volume**: +1 point per 100k volume.
5. **Hard Limit**: Score is 0 if Current Debt > Approved Limit.

## Running Tests
```bash
docker-compose run web python manage.py test
```
