from .models import Customer, Loan
from datetime import datetime
from django.db.models import Sum

def calculate_monthly_installment(principal, annual_interest_rate, tenure_months):
    """
    Calculates EMI using formula: E = P * r * (1+r)^n / ((1+r)^n - 1)
    """
    if annual_interest_rate <= 0 or tenure_months <= 0:
        return 0
        
    r = annual_interest_rate / 12 / 100
    n = tenure_months
    
    numerator = principal * r * ((1 + r) ** n)
    denominator = ((1 + r) ** n) - 1
    
    return numerator / denominator

def calculate_credit_score(customer_id):
    """
    Calculates credit score based on historical data.
    """
    try:
        customer = Customer.objects.get(customer_id=customer_id)
        loans = Loan.objects.filter(customer=customer)
        
        # Factor 1: Past Loans Paid on Time
        # Assuming we sum up 'emis_paid_on_time' from all loans? 
        # Or just checking if they have good history.
        # Plan proposal: +0.5 points per EMI paid on time.
        total_emis_paid_on_time = loans.aggregate(Sum('emis_paid_on_time'))['emis_paid_on_time__sum'] or 0
        
        # Factor 2: Number of Loans
        # Plan: +5 points per completed loan? Or just total loans taken?
        # Prompt says "Number of loans taken in the past".
        total_loans = loans.count()
        
        # Factor 3: Loan activity in the current year
        current_year = datetime.now().year
        loans_this_year = loans.filter(start_date__year=current_year).count()
        
        # Factor 4: Loan approved volume
        total_approved_volume = loans.aggregate(Sum('loan_amount'))['loan_amount__sum'] or 0
        
        # Calculation
        # If no loan history, give a base score (new customer benefit)
        if total_loans == 0:
            score = 50  # New customers start with a neutral score
        else:
            score = 0
            score += (total_emis_paid_on_time * 0.5)
            score += (total_loans * 5)
            score -= (loans_this_year * 10) # Penalty for too much recent activity
            score += (total_approved_volume / 100000) # 1 point per 100k
        
        # Cap at 100
        score = min(score, 100)
        score = max(score, 0) # No negative scores
        
        # CRITICAL RULE: If sum(current_loans) > approved_limit, Credit Score = 0
        # "current_loans" implies current debt/outstanding amount.
        # Using model field 'current_debt' (if ingested accurately) OR summing loan_amounts?
        # Let's use the 'current_debt' field from Customer model as it's explicit.
        if customer.current_debt > (customer.approved_limit or 0):
            score = 0
            
        return score
        
    except Customer.DoesNotExist:
        return 0

def check_loan_eligibility(customer_id, loan_amount, interest_rate, tenure):
    try:
        customer = Customer.objects.get(customer_id=customer_id)
    except Customer.DoesNotExist:
        return {"error": "Customer not found"}

    credit_score = calculate_credit_score(customer_id)
    
    approval = False
    corrected_interest_rate = interest_rate
    
    if credit_score > 50:
        approval = True
    elif 50 >= credit_score > 30:
        if interest_rate > 12:
            approval = True
        else:
            approval = True
            corrected_interest_rate = 12.0
    elif 30 >= credit_score > 10:
        if interest_rate > 16:
            approval = True
        else:
            approval = True
            corrected_interest_rate = 16.0
    else: # Score <= 10
        approval = False
    
    # Salary Rule
    try:
        active_loans = Loan.objects.filter(customer=customer, end_date__gt=datetime.now().date())
        current_emis = active_loans.aggregate(Sum('monthly_repayment'))['monthly_repayment__sum'] or 0
        
        if current_emis > (0.5 * customer.monthly_salary):
            approval = False
    except Exception:
        pass # Should handle gracefully
        
    monthly_installment = calculate_monthly_installment(loan_amount, corrected_interest_rate, tenure)
    
    return {
        "customer_id": customer_id,
        "approval": approval,
        "interest_rate": interest_rate,
        "corrected_interest_rate": corrected_interest_rate,
        "tenure": tenure,
        "monthly_installment": monthly_installment
    }
