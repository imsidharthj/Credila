from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import CustomerRegistrationSerializer
from .models import Customer

@api_view(['POST'])
def register_customer(request):
    serializer = CustomerRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        customer = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from .serializers import LoanEligibilitySerializer
from .utils import check_loan_eligibility
from .models import Loan
import datetime
from dateutil.relativedelta import relativedelta

@api_view(['POST'])
def check_eligibility(request):
    serializer = LoanEligibilitySerializer(data=request.data)
    if serializer.is_valid():
        data = serializer.validated_data
        result = check_loan_eligibility(
            data['customer_id'],
            data['loan_amount'],
            data['interest_rate'],
            data['tenure']
        )
        
        if "error" in result:
             return Response(result, status=status.HTTP_404_NOT_FOUND)
             
        return Response(result, status=status.HTTP_200_OK)
        
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def create_loan(request):
    serializer = LoanEligibilitySerializer(data=request.data)
    if serializer.is_valid():
        data = serializer.validated_data
        customer_id = data['customer_id']
        loan_amount = data['loan_amount']
        interest_rate = data['interest_rate']
        tenure = data['tenure']
        
        # Check eligibility
        result = check_loan_eligibility(
            customer_id,
            loan_amount,
            interest_rate,
            tenure
        )
        
        if "error" in result:
             return Response(result, status=status.HTTP_404_NOT_FOUND)
        
        if result['approval']:
            # Create Loan
            customer = Customer.objects.get(customer_id=customer_id)
            start_date = datetime.date.today()
            end_date = start_date + relativedelta(months=tenure)
            
            loan = Loan.objects.create(
                customer=customer,
                loan_amount=loan_amount,
                tenure=tenure,
                interest_rate=result['corrected_interest_rate'], # Use corrected rate
                monthly_repayment=result['monthly_installment'],
                start_date=start_date,
                end_date=end_date,
                emis_paid_on_time=0
            )
            
            # Update customer debt? Not strictly required by prompt but logical.
            # "current_debt" usually implies principal outstanding.
            # We'll stick to just creating the loan as per requirements.
            
            return Response({
                "loan_id": loan.loan_id,
                "customer_id": customer_id,
                "loan_approved": True,
                "message": "Loan approved",
                "monthly_installment": result['monthly_installment']
            }, status=status.HTTP_201_CREATED)
            
        else:
            return Response({
                "loan_id": None,
                "customer_id": customer_id,
                "loan_approved": False,
                "message": "Loan not approved based on eligibility rules",
                "monthly_installment": 0
            }, status=status.HTTP_200_OK) # Or 400? Spec doesn't say. 200 with approved: false is common.
            
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from .serializers import LoanDetailSerializer, LoanListSerializer

@api_view(['GET'])
def view_loan(request, loan_id):
    try:
        loan = Loan.objects.get(loan_id=loan_id)
        serializer = LoanDetailSerializer(loan)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Loan.DoesNotExist:
        return Response({"error": "Loan not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def view_all_loans(request, customer_id):
    # Verify customer exists? Not strictly necessary if we just return empty list, but better.
    # But filtering by key doesn't raise error.
    loans = Loan.objects.filter(customer_id=customer_id)
    serializer = LoanListSerializer(loans, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
