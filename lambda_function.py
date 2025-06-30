import xmlrpc.client
import json
import os
import smtplib
from email.mime.text import MIMEText

# --- Odoo Connection Configuration ---
ODOO_URL = os.environ.get('ODOO_URL')
ODOO_DB = os.environ.get('ODOO_DB')
ODOO_USERNAME = os.environ.get('ODOO_USERNAME')
ODOO_PASSWORD = os.environ.get('ODOO_PASSWORD')

# --- Gmail SMTP Notification Configuration ---
GMAIL_EMAIL = os.environ.get('GMAIL_EMAIL')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD')
NOTIFICATION_EMAIL = os.environ.get('NOTIFICATION_EMAIL')

# --- Client Authentication Configuration ---
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')


def lambda_handler(event, context):
    """
    Main handler function for AWS Lambda.
    Creates an Opportunity in Odoo and sends an email notification via Gmail.
    Compatible with Lambda Function URLs.
    """
    
    # --- MODIFICATION: Removed manual CORS headers dictionary ---
    
    request_context = event.get('requestContext', {})
    http_method = request_context.get('http', {}).get('method')

    # The browser might still send an OPTIONS request for preflight check.
    # The Lambda Function URL CORS config will handle this, but we can exit early.
    if http_method == 'OPTIONS':
        return {'statusCode': 204} # No body or headers needed
        
    if http_method != 'POST':
        # Removed 'headers' from this return statement
        return {'statusCode': 405, 'body': json.dumps({'error': 'Method Not Allowed'})}

    # --- Step 0: Authenticate the client request ---
    if CLIENT_ID and CLIENT_SECRET:
        request_headers = event.get('headers', {})
        received_client_id = request_headers.get('x-client-id')
        received_client_secret = request_headers.get('x-client-secret')

        if not (received_client_id == CLIENT_ID and received_client_secret == CLIENT_SECRET):
            print("Authentication failed: Invalid client ID or secret.")
            # Removed 'headers' from this return statement
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Unauthorized'})
            }

    try:
        data = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        # Removed 'headers' from this return statement
        return {'statusCode': 400, 'body': json.dumps({'error': 'Invalid request body. Expecting JSON.'})}

    data['type'] = 'opportunity'

    # --- Step 1: Authenticate with Odoo ---
    try:
        common = xmlrpc.client.ServerProxy(f'https://{ODOO_URL}/xmlrpc/2/common')
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
        if not uid:
            raise Exception("Authentication failed. Please check credentials.")
    except Exception as e:
        print(f"Odoo Authentication Error: {e}")
        # Removed 'headers' from this return statement
        return {'statusCode': 500, 'body': json.dumps({'error': f'Could not authenticate with Odoo: {e}'})}

    # --- Step 2: Create the Opportunity in Odoo ---
    lead_id = None
    try:
        models = xmlrpc.client.ServerProxy(f'https://{ODOO_URL}/xmlrpc/2/object')
        lead_id = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'crm.lead', 'create', [data])
        print(f"Successfully created opportunity with ID: {lead_id}")
        
    except xmlrpc.client.Fault as e:
        print(f"Odoo API Error during record creation: {e}")
        # Removed 'headers' from this return statement
        return {'statusCode': 500, 'body': json.dumps({'error': f'Odoo API error: {e.faultString}'})}
    except Exception as e:
        print(f"An unexpected error occurred during Odoo creation: {e}")
        # Removed 'headers' from this return statement
        return {'statusCode': 500, 'body': json.dumps({'error': 'An unexpected server error occurred.'})}

    # --- Step 3: Send an Email Notification (Temporarily Disabled) ---
    # The email sending logic would go here when re-enabled.

    # MODIFICATION: Removed 'headers' from the final success return statement.
    return {
        'statusCode': 200,
        'body': json.dumps({
            'success': True,
            'message': 'Opportunity created successfully!',
            'leadId': lead_id
        })
    }