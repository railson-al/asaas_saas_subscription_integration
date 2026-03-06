import requests
from django.conf import settings
from rest_framework.exceptions import APIException

class AsaasAPIException(APIException):
    status_code = 503
    default_detail = 'Service temporarily unavailable, try again later.'
    default_code = 'service_unavailable'

def get_asaas_headers():
    return {
        'access_token': settings.ASAAS_API_KEY,
        'Content-Type': 'application/json'
    }

def create_customer(user, cpf_cnpj=None):
    url = f"{settings.ASAAS_API_URL}/customers"
    payload = {
        "name": user.get_full_name() or user.username,
        "email": user.email,
    }
    
    if cpf_cnpj:
        payload["cpfCnpj"] = cpf_cnpj

    
    response = requests.post(url, json=payload, headers=get_asaas_headers())
    
    if response.status_code in [200, 201]:
        return response.json().get('id')
    else:
        # Log error
        raise AsaasAPIException(detail=f"Error creating Asaas customer: {response.text}")

def create_payment(customer_id, billing_type, value, due_date, description=""):
    url = f"{settings.ASAAS_API_URL}/payments"
    payload = {
        "customer": customer_id,
        "billingType": billing_type,
        "value": float(value),
        "dueDate": due_date.strftime("%Y-%m-%d"),
        "description": description
    }
    
    response = requests.post(url, json=payload, headers=get_asaas_headers())
    if response.status_code in [200, 201]:
        return response.json()
    else:
        raise AsaasAPIException(detail=f"Error creating Asaas payment: {response.text}")

def get_pix_qrcode(payment_id):
    url = f"{settings.ASAAS_API_URL}/payments/{payment_id}/pixQrCode"
    response = requests.get(url, headers=get_asaas_headers())
    if response.status_code == 200:
        return response.json()
    else:
        raise AsaasAPIException(detail=f"Error getting Pix QR Code: {response.text}")

def create_subscription(customer_id, billing_type, value, cycle, next_due_date, description=""):
    url = f"{settings.ASAAS_API_URL}/subscriptions"
    payload = {
        "customer": customer_id,
        "billingType": billing_type,
        "value": float(value),
        "nextDueDate": next_due_date.strftime("%Y-%m-%d"),
        "cycle": cycle,
        "description": description
    }
    
    response = requests.post(url, json=payload, headers=get_asaas_headers())
    if response.status_code in [200, 201]:
        return response.json()
    else:
        raise AsaasAPIException(detail=f"Error creating Asaas subscription: {response.text}")

def update_subscription(subscription_id, value, cycle, next_due_date):
    url = f"{settings.ASAAS_API_URL}/subscriptions/{subscription_id}"
    payload = {
        "value": float(value),
        "cycle": cycle,
        "nextDueDate": next_due_date.strftime("%Y-%m-%d"),
    }
    
    # According to Asaas docs, update is POST to /v3/subscriptions/{id} (or PUT technically supported, defaulting to POST)
    response = requests.post(url, json=payload, headers=get_asaas_headers())
    
    if response.status_code in [200, 201]:
        return response.json()
    else:
        raise AsaasAPIException(detail=f"Error updating Asaas subscription: {response.text}")

def cancel_subscription(subscription_id):
    url = f"{settings.ASAAS_API_URL}/subscriptions/{subscription_id}"
    response = requests.delete(url, headers=get_asaas_headers())
    
    if response.status_code in [200, 201]:
        return response.json()
    else:
        raise AsaasAPIException(detail=f"Error canceling Asaas subscription: {response.text}")

def get_subscription(subscription_id):
    url = f"{settings.ASAAS_API_URL}/subscriptions/{subscription_id}"
    response = requests.get(url, headers=get_asaas_headers())
    if response.status_code == 200:
        return response.json()
    raise AsaasAPIException(detail=f"Error getting Asaas subscription: {response.text}")

def get_payment(payment_id):
    url = f"{settings.ASAAS_API_URL}/payments/{payment_id}"
    response = requests.get(url, headers=get_asaas_headers())
    if response.status_code == 200:
        return response.json()
    raise AsaasAPIException(detail=f"Error getting Asaas payment: {response.text}")

def get_subscription_payments(subscription_id):
    url = f"{settings.ASAAS_API_URL}/subscriptions/{subscription_id}/payments"
    response = requests.get(url, headers=get_asaas_headers())
    if response.status_code == 200:
        return response.json()
    raise AsaasAPIException(detail=f"Error getting Asaas subscription payments: {response.text}")



