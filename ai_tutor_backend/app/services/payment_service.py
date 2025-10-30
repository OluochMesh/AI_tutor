# app/services/mpesa_service.py - Daraja M-Pesa Integration

import os
import requests
import base64
from datetime import datetime
import json

class MpesaService:
    def __init__(self):
        
        # Environment
        self.environment = os.environ.get('MPESA_ENVIRONMENT', 'sandbox')  # 'sandbox' or 'production'
        
        # API Credentials
        self.consumer_key = os.environ.get('MPESA_CONSUMER_KEY', '')
        self.consumer_secret = os.environ.get('MPESA_CONSUMER_SECRET', '')
        
        # Business Configuration
        self.shortcode = os.environ.get('MPESA_SHORTCODE', '')  # Your business shortcode
        self.passkey = os.environ.get('MPESA_PASSKEY', '')  # Lipa Na M-Pesa Online Passkey
        
        # Callback URLs
        self.callback_url = os.environ.get('MPESA_CALLBACK_URL', 'https://ashlee-nonexecutable-jack.ngrok-free.dev/api/subscription/mpesa-callback')
        
        # API URLs
        if self.environment == 'sandbox':
            self.base_url = 'https://sandbox.safaricom.co.ke'
        else:
            self.base_url = 'https://api.safaricom.co.ke'
        
        self.auth_url = f'{self.base_url}/oauth/v1/generate?grant_type=client_credentials'
        self.stk_push_url = f'{self.base_url}/mpesa/stkpush/v1/processrequest'
        self.stk_query_url = f'{self.base_url}/mpesa/stkpushquery/v1/query'
    
    def get_access_token(self):
        """Get OAuth access token from Daraja API"""
        try:
            # Create basic auth string
            auth_string = f"{self.consumer_key}:{self.consumer_secret}"
            auth_bytes = auth_string.encode('utf-8')
            auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
            
            headers = {
                'Authorization': f'Basic {auth_base64}'
            }
            
            response = requests.get(self.auth_url, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            return result.get('access_token')
            
        except Exception as e:
            print(f"Failed to get access token: {str(e)}")
            return None
    
    def generate_password(self):
        """Generate password for STK Push"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password_string = f"{self.shortcode}{self.passkey}{timestamp}"
        password_bytes = password_string.encode('utf-8')
        password_base64 = base64.b64encode(password_bytes).decode('utf-8')
        return password_base64, timestamp
    
    def initiate_stk_push(self, phone_number, amount, account_reference, transaction_desc):
        """
        Initiate STK Push (Lipa Na M-Pesa Online)
        
        Args:
            phone_number (str): Phone number in format 254XXXXXXXXX
            amount (int): Amount in KES
            account_reference (str): Reference (e.g., user ID)
            transaction_desc (str): Description
            
        Returns:
            dict: Response with checkout_request_id or error
        """
        try:
            # Get access token
            access_token = self.get_access_token()
            if not access_token:
                return {'success': False, 'error': 'Failed to authenticate with M-Pesa'}
            
            # Generate password and timestamp
            password, timestamp = self.generate_password()
            
            # Prepare request
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'BusinessShortCode': self.shortcode,
                'Password': password,
                'Timestamp': timestamp,
                'TransactionType': 'CustomerPayBillOnline',
                'Amount': int(amount),
                'PartyA': phone_number,
                'PartyB': self.shortcode,
                'PhoneNumber': phone_number,
                'CallBackURL': self.callback_url,
                'AccountReference': account_reference,
                'TransactionDesc': transaction_desc
            }
            
            response = requests.post(
                self.stk_push_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            result = response.json()
            
            if result.get('ResponseCode') == '0':
                return {
                    'success': True,
                    'checkout_request_id': result.get('CheckoutRequestID'),
                    'merchant_request_id': result.get('MerchantRequestID'),
                    'message': 'STK push sent successfully'
                }
            else:
                return {
                    'success': False,
                    'error': result.get('ResponseDescription', 'STK push failed')
                }
                
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f'Network error: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'STK push failed: {str(e)}'}
    
    def query_stk_status(self, checkout_request_id):
        """
        Query STK Push transaction status
        
        Args:
            checkout_request_id (str): CheckoutRequestID from STK push
            
        Returns:
            dict: Transaction status
        """
        try:
            # Get access token
            access_token = self.get_access_token()
            if not access_token:
                return {'success': False, 'error': 'Failed to authenticate'}
            
            # Generate password and timestamp
            password, timestamp = self.generate_password()
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'BusinessShortCode': self.shortcode,
                'Password': password,
                'Timestamp': timestamp,
                'CheckoutRequestID': checkout_request_id
            }
            
            response = requests.post(
                self.stk_query_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            result = response.json()
            
            # ResultCode meanings:
            # 0 = Success
            # 1032 = Request cancelled by user
            # 1037 = Timeout
            # Other = Failed
            
            result_code = result.get('ResultCode')
            
            if result_code == '0':
                status = 'COMPLETED'
            elif result_code == '1032':
                status = 'CANCELLED'
            elif result_code == '1037':
                status = 'TIMEOUT'
            elif result_code is None:
                status = 'PENDING'
            else:
                status = 'FAILED'
            
            return {
                'success': True,
                'status': status,
                'result_code': result_code,
                'result_desc': result.get('ResultDesc', ''),
                'checkout_request_id': checkout_request_id
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Query failed: {str(e)}'}
    
    def validate_phone_number(self, phone_number):
        """Validate and format phone number"""
        # Remove spaces and special characters
        phone = phone_number.replace(' ', '').replace('-', '').replace('+', '')
        
        # Convert 07XX to 2547XX or 01XX to 2541XX
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        
        # Check if valid Kenyan number
        if not phone.startswith('254') or len(phone) != 12:
            return None
        
        return phone