#!/usr/bin/env python3
"""
Test script for M-Pesa integration
Run this script to verify M-Pesa API connection and functionality.

Usage:
    python test_mpesa_integration.py

Make sure to set the following environment variables:
    - MPESA_ENVIRONMENT (sandbox or production)
    - MPESA_CONSUMER_KEY
    - MPESA_CONSUMER_SECRET
    - MPESA_SHORTCODE
    - MPESA_PASSKEY
    - MPESA_CALLBACK_URL
"""

import os
import sys
from app import create_app
from app.services.payment_service import MpesaService
from app.extension import db

def test_access_token():
    """Test 1: Verify access token generation"""
    print("\n" + "="*60)
    print("TEST 1: Access Token Generation")
    print("="*60)
    
    mpesa = MpesaService()
    token = mpesa.get_access_token()
    
    if token:
        print(f"✅ SUCCESS: Access token obtained")
        print(f"   Token (first 20 chars): {token[:20]}...")
        return True
    else:
        print("❌ FAILED: Could not obtain access token")
        print("   Check your MPESA_CONSUMER_KEY and MPESA_CONSUMER_SECRET")
        return False

def test_phone_validation():
    """Test 2: Verify phone number validation"""
    print("\n" + "="*60)
    print("TEST 2: Phone Number Validation")
    print("="*60)
    
    mpesa = MpesaService()
    
    test_cases = [
        ("0712345678", "254712345678"),
        ("254712345678", "254712345678"),
        ("+254712345678", "254712345678"),
        ("07 123 456 78", "254712345678"),
        ("123", None),  # Invalid
        ("", None),  # Invalid
    ]
    
    all_passed = True
    for input_phone, expected in test_cases:
        result = mpesa.validate_phone_number(input_phone)
        if result == expected:
            print(f"✅ {input_phone} -> {result}")
        else:
            print(f"❌ {input_phone} -> {result} (expected {expected})")
            all_passed = False
    
    return all_passed

def test_configuration():
    """Test 3: Verify configuration"""
    print("\n" + "="*60)
    print("TEST 3: Configuration Check")
    print("="*60)
    
    required_vars = [
        'MPESA_ENVIRONMENT',
        'MPESA_CONSUMER_KEY',
        'MPESA_CONSUMER_SECRET',
        'MPESA_SHORTCODE',
        'MPESA_PASSKEY',
        'MPESA_CALLBACK_URL'
    ]
    
    all_set = True
    for var in required_vars:
        value = os.environ.get(var, '')
        if value:
            # Mask sensitive values
            if 'KEY' in var or 'SECRET' in var or 'PASSKEY' in var:
                display_value = value[:4] + "..." if len(value) > 4 else "***"
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NOT SET")
            all_set = False
    
    return all_set

def test_stk_push_simulation():
    """Test 4: Simulate STK Push (without actually sending)"""
    print("\n" + "="*60)
    print("TEST 4: STK Push Simulation")
    print("="*60)
    
    mpesa = MpesaService()
    
    # Check if we have credentials
    if not mpesa.consumer_key or not mpesa.consumer_secret:
        print("⚠️  SKIPPED: Credentials not configured")
        return None
    
    # Test password generation
    password, timestamp = mpesa.generate_password()
    print(f"✅ Password generated: {password[:20]}...")
    print(f"✅ Timestamp: {timestamp}")
    
    # Test access token
    token = mpesa.get_access_token()
    if token:
        print(f"✅ Access token obtained")
        print("⚠️  NOTE: To test actual STK push, use a real phone number")
        print("   This test only verifies the setup, not actual payment")
        return True
    else:
        print("❌ Could not get access token")
        return False

def test_database_models():
    """Test 5: Verify database models"""
    print("\n" + "="*60)
    print("TEST 5: Database Models")
    print("="*60)
    
    app = create_app()
    with app.app_context():
        try:
            from app.models import Payment
            # Check if table exists
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'payments' in tables:
                print("✅ Payments table exists")
                
                # Check columns
                columns = [col['name'] for col in inspector.get_columns('payments')]
                required_columns = [
                    'id', 'user_id', 'checkout_request_id', 'amount',
                    'status', 'mpesa_receipt_number'
                ]
                
                missing = [col for col in required_columns if col not in columns]
                if missing:
                    print(f"❌ Missing columns: {missing}")
                    print("   Run database migrations: flask db upgrade")
                    return False
                else:
                    print("✅ All required columns present")
                    return True
            else:
                print("❌ Payments table does not exist")
                print("   Run database migrations: flask db upgrade")
                return False
        except Exception as e:
            print(f"❌ Error checking database: {str(e)}")
            return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("M-PESA INTEGRATION TEST SUITE")
    print("="*60)
    
    results = {}
    
    # Test 1: Configuration
    results['configuration'] = test_configuration()
    
    # Test 2: Phone validation
    results['phone_validation'] = test_phone_validation()
    
    # Test 3: Access token
    if results['configuration']:
        results['access_token'] = test_access_token()
    else:
        print("\n⚠️  Skipping access token test (configuration incomplete)")
        results['access_token'] = None
    
    # Test 4: STK Push simulation
    if results.get('access_token'):
        results['stk_simulation'] = test_stk_push_simulation()
    else:
        results['stk_simulation'] = None
    
    # Test 5: Database
    results['database'] = test_database_models()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v is True)
    total = sum(1 for v in results.values() if v is not None)
    
    for test_name, result in results.items():
        if result is True:
            status = "✅ PASSED"
        elif result is False:
            status = "❌ FAILED"
        else:
            status = "⚠️  SKIPPED"
        print(f"{test_name.replace('_', ' ').title():30} {status}")
    
    print("\n" + "="*60)
    if passed == total and total > 0:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        return 0
    elif total == 0:
        print("⚠️  NO TESTS RUN (configuration incomplete)")
        return 1
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total} passed)")
        return 1

if __name__ == '__main__':
    sys.exit(main())

