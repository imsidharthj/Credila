from rest_framework import serializers
from .models import Customer, Loan

class CustomerRegistrationSerializer(serializers.ModelSerializer):
    monthly_income = serializers.IntegerField(source='monthly_salary')

    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'age', 'monthly_income', 'phone_number']

    def create(self, validated_data):
        # Calculate approved_limit
        # Rule: 36 * monthly_salary, rounded to nearest lakh
        salary = validated_data.get('monthly_salary')
        limit = 36 * salary
        
        # Round to nearest 100,000 (Lakh)
        # Assuming standard mathematical rounding (or floor/ceil? Prompt says "Rounded to nearest Lakh")
        # Python's round() rounds to nearest even number for .5 cases, usually acceptable.
        # But 'nearest lakh' logic: round(limit / 100000) * 100000
        
        approved_limit = round(limit / 100000) * 100000
        
        validated_data['approved_limit'] = approved_limit
        
        return super().create(validated_data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['approved_limit'] = instance.approved_limit
        ret['customer_id'] = instance.customer_id
        # Include customer_id and approved_limit in response as requested
        return ret

class LoanEligibilitySerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    loan_amount = serializers.FloatField()
    interest_rate = serializers.FloatField()
    tenure = serializers.IntegerField()

class CustomerDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'phone_number', 'age']

class LoanDetailSerializer(serializers.ModelSerializer):
    customer = CustomerDetailSerializer(read_only=True)
    
    class Meta:
        model = Loan
        fields = ['loan_id', 'customer', 'loan_amount', 'interest_rate', 'monthly_repayment', 'tenure']

class LoanListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = ['loan_id', 'loan_amount', 'interest_rate', 'monthly_repayment', 'repayments_left']
        
    repayments_left = serializers.SerializerMethodField()
    
    def get_repayments_left(self, obj):
        return obj.tenure - obj.emis_paid_on_time
