import xmlrpc.client
import json
import os
import boto3

# --- Odoo Connection Configuration ---
ODOO_URL = os.environ.get('ODOO_URL')
ODOO_DB = os.environ.get('ODOO_DB')
ODOO_USERNAME = os.environ.get('ODOO_USERNAME')
ODOO_PASSWORD = os.environ.get('ODOO_PASSWORD')

# --- AWS SES Email Notification Configuration ---
SENDER_EMAIL = os.environ.get('SENDER_EMAIL')             # The 'From' email address. Must be a verified identity in AWS SES (e.g., info@mohankrushiudyog.com).
NOTIFICATION_EMAIL = os.environ.get('NOTIFICATION_EMAIL') # A comma-separated list of recipient emails.
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')    # The AWS region where you use SES.

# --- Client Authentication Configuration ---
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')


def lambda_handler(event, context):
    """
    Main handler function for AWS Lambda.
    Creates an Opportunity in Odoo and sends an email notification via AWS SES.
    Compatible with Lambda Function URLs.
    """
    
    request_context = event.get('requestContext', {})
    http_method = request_context.get('http', {}).get('method')

    if http_method == 'OPTIONS':
        return {'statusCode': 204}
        
    if http_method != 'POST':
        return {'statusCode': 405, 'body': json.dumps({'error': 'Method Not Allowed'})}

    # --- Step 0: Authenticate the client request ---
    if CLIENT_ID and CLIENT_SECRET:
        request_headers = event.get('headers', {})
        received_client_id = request_headers.get('x-client-id')
        received_client_secret = request_headers.get('x-client-secret')

        if not (received_client_id == CLIENT_ID and received_client_secret == CLIENT_SECRET):
            print("Authentication failed: Invalid client ID or secret.")
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Unauthorized'})
            }

    try:
        data = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
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
        return {'statusCode': 500, 'body': json.dumps({'error': f'Could not authenticate with Odoo: {e}'})}

    # --- Step 2: Create the Opportunity in Odoo ---
    lead_id = None
    try:
        models = xmlrpc.client.ServerProxy(f'https://{ODOO_URL}/xmlrpc/2/object')
        lead_id = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'crm.lead', 'create', [data])
        print(f"Successfully created opportunity with ID: {lead_id}")
        
    except xmlrpc.client.Fault as e:
        print(f"Odoo API Error during record creation: {e}")
        return {'statusCode': 500, 'body': json.dumps({'error': f'Odoo API error: {e.faultString}'})}
    except Exception as e:
        print(f"An unexpected error occurred during Odoo creation: {e}")
        return {'statusCode': 500, 'body': json.dumps({'error': 'An unexpected server error occurred.'})}

    # --- Step 3: Send an Email Notification using AWS SES ---
    if lead_id and SENDER_EMAIL and NOTIFICATION_EMAIL:
        try:
            recipient_list = [email.strip() for email in NOTIFICATION_EMAIL.split(',') if email.strip()]
            
            if not recipient_list:
                print("Warning: NOTIFICATION_EMAIL variable is set but contains no valid email addresses.")
            else:
                ses_client = boto3.client('ses', region_name=AWS_REGION)
                
                subject = f"New Website Opportunity: {data.get('name', 'N/A')}"
                
                # Create a nicely formatted HTML body for the email
                html_body = f"""
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; color: #333; }}
                        .container {{ max-width: 600px; margin: 20px auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px; background-color: #fdfdfd; }}
                        h2 {{ color: #005a2b; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
                        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                        th, td {{ text-align: left; padding: 12px; border-bottom: 1px solid #eee; }}
                        th {{ background-color: #f9f9f9; width: 30%; font-weight: bold; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h2>New Website Opportunity Received</h2>
                        <p>A new opportunity has been created from the website contact form. Here are the details:</p>
                        <table>
                            <tr>
                                <th>Opportunity Title</th>
                                <td>{data.get('name', 'N/A')}</td>
                            </tr>
                            <tr>
                                <th>Contact Name</th>
                                <td>{data.get('contact_name', 'N/A')}</td>
                            </tr>
                            <tr>
                                <th>Email</th>
                                <td>{data.get('email_from', 'N/A')}</td>
                            </tr>
                            <tr>
                                <th>Phone</th>
                                <td>{data.get('phone', 'N/A')}</td>
                            </tr>
                            <tr>
                                <th>Message</th>
                                <td><pre style="font-family: Arial, sans-serif; margin: 0; white-space: pre-wrap;">{data.get('description', 'N/A')}</pre></td>
                            </tr>
                            <tr>
                                <th>Odoo ID</th>
                                <td>{lead_id}</td>
                            </tr>
                        </table>
                        <p style="margin-top: 20px; font-size: 12px; color: #888;">This is an automated notification from mohankrushiudyog.com.</p>
                    </div>
                </body>
                </html>
                """
                
                ses_client.send_email(
                    Source=SENDER_EMAIL,
                    Destination={'ToAddresses': recipient_list},
                    Message={
                        'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                        'Body': {
                            'Html': {'Data': html_body, 'Charset': 'UTF-8'}
                        }
                    }
                )
                print(f"Successfully sent SES notification to: {', '.join(recipient_list)}")
        
        except Exception as e:
            # If email fails, just log the error but don't fail the entire function.
            print(f"Failed to send SES notification email. Error: {e}")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'success': True,
            'message': 'Opportunity created successfully!',
            'leadId': lead_id
        })
    }
