import requests
import logging
from config import Config
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NowPaymentsAPI:
    BASE_URL = "https://api.nowpayments.io/v1"
    
    def __init__(self):
        self.api_key = Config.NOW_PAYMENTS_API_KEY
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    def create_payment(self, price_amount, user_id):
        """
        Create a payment for deposit.
        
        Args:
            price_amount (float): Amount in USDT
            user_id (str): Firebase user ID for reference
            
        Returns:
            dict: Payment details including payment URL
        """
        try:
            endpoint = f"{self.BASE_URL}/payment"
            
            payload = {
                "price_amount": price_amount,
                "price_currency": "usd",  # Using USD as base currency
                "pay_currency": "usdt",   # Accept payment in USDT
                "order_id": f"deposit_{user_id}_{datetime.now().timestamp()}",
                "order_description": f"Deposit for user {user_id}",
                "ipn_callback_url": "https://your-domain.com/nowpayments/callback",  # Replace with actual callback URL
                "success_url": "https://your-domain.com/deposit/success",  # Replace with actual success URL
                "cancel_url": "https://your-domain.com/deposit/cancel"     # Replace with actual cancel URL
            }
            
            response = requests.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating payment: {str(e)}")
            raise

    def create_withdrawal(self, address, amount, user_id):
        """
        Create a withdrawal payout.
        
        Args:
            address (str): USDT wallet address
            amount (float): Amount to withdraw in USDT
            user_id (str): Firebase user ID for reference
            
        Returns:
            dict: Payout details
        """
        try:
            endpoint = f"{self.BASE_URL}/payout"
            
            payload = {
                "withdrawals": [{
                    "address": address,
                    "currency": "usdt",
                    "amount": amount,
                    "ipn_callback_url": "https://your-domain.com/nowpayments/payout-callback",  # Replace with actual callback URL
                    "payload": {
                        "user_id": user_id,
                        "timestamp": datetime.now().isoformat()
                    }
                }]
            }
            
            response = requests.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating withdrawal: {str(e)}")
            raise

    def get_payment_status(self, payment_id):
        """
        Check the status of a payment.
        
        Args:
            payment_id (str): Payment ID from create_payment response
            
        Returns:
            dict: Payment status details
        """
        try:
            endpoint = f"{self.BASE_URL}/payment/{payment_id}"
            
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting payment status: {str(e)}")
            raise

    def get_minimum_payment_amount(self):
        """
        Get minimum payment amount for USDT.
        
        Returns:
            float: Minimum payment amount
        """
        try:
            endpoint = f"{self.BASE_URL}/min-amount"
            params = {"currency_from": "usdt"}
            
            response = requests.get(endpoint, params=params, headers=self.headers)
            response.raise_for_status()
            
            return float(response.json().get('min_amount', 0))
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting minimum payment amount: {str(e)}")
            raise

    def verify_callback(self, ipn_data):
        """
        Verify IPN callback authenticity.
        
        Args:
            ipn_data (dict): Callback data received from Now Payments
            
        Returns:
            bool: True if callback is authentic, False otherwise
        """
        try:
            # Get the authentication key from the header
            auth_key = ipn_data.get('verification_key')
            
            # Verify the key matches your stored key
            endpoint = f"{self.BASE_URL}/payment-verification/{auth_key}"
            
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            
            return response.json().get('verification_status') == 'confirmed'
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error verifying callback: {str(e)}")
            return False

    def process_callback(self, callback_data):
        """
        Process IPN callback data.
        
        Args:
            callback_data (dict): Callback data received from Now Payments
            
        Returns:
            dict: Processed payment information
        """
        try:
            payment_status = callback_data.get('payment_status')
            order_id = callback_data.get('order_id')
            
            if not order_id or not payment_status:
                raise ValueError("Invalid callback data")
            
            # Extract user_id from order_id (format: deposit_user_id_timestamp)
            user_id = order_id.split('_')[1]
            
            return {
                'user_id': user_id,
                'status': payment_status,
                'amount': callback_data.get('actually_paid'),
                'currency': callback_data.get('pay_currency'),
                'timestamp': callback_data.get('created_at')
            }
            
        except Exception as e:
            logger.error(f"Error processing callback data: {str(e)}")
            raise

# Create a singleton instance
now_payments = NowPaymentsAPI()