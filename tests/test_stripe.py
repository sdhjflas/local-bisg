#!/usr/bin/env python3
"""Minimal Stripe test"""

from dotenv import load_dotenv
load_dotenv()

import os
import stripe

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

print(f"Stripe module: {stripe}")
print(f"API key loaded: {bool(stripe.api_key)}")

# Test creating a checkout session
try:
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': 'Test Product',
                },
                'unit_amount': 10000,
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url='https://example.com/success',
        cancel_url='https://example.com/cancel',
    )
    print(f"\n✅ SUCCESS! Created session: {session.id}")
    print(f"URL: {session.url[:60]}...")
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
