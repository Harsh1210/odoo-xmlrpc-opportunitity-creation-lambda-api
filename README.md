# Serverless Odoo CRM Connector

This project provides a secure, serverless solution for connecting a frontend web form directly to your Odoo CRM. It uses an AWS Lambda function written in Python to receive form submissions and create new opportunities in Odoo, without the need to manage a dedicated backend server.

## Features

-   **Direct Odoo Integration:** Creates Opportunities directly in the Odoo CRM pipeline.
-   **Serverless Architecture:** Low-cost, scalable, and maintenance-free, powered by AWS Lambda.
-   **Secure Endpoint:** Uses a Client ID and Secret to protect the public-facing Lambda Function URL from unauthorized access.
-   **HTML Email Notifications:** Can be configured to send formatted email notifications for new opportunities using AWS Simple Email Service (SES).
-   **Decoupled:** The frontend and backend are completely separate, allowing you to use any web technology (React, Vue, plain HTML, etc.).

## Architecture Flow

The data flows from the user's browser to your Odoo CRM in the following sequence:

1.  **Frontend Form**: A user submits the contact form on your website.
2.  **HTTPS Request**: The frontend sends a `POST` request to the AWS Lambda Function URL, including the form data and security credentials in the headers.
3.  **AWS Lambda**: The Python function is triggered. It validates the client credentials, authenticates with your Odoo instance, creates a new opportunity, and sends a notification via SES.
4.  **Odoo CRM**: The new opportunity appears in your CRM pipeline, ready for your sales team.

```bash
[User on Website] --> [React App] --> [AWS Lambda Function URL] --> [Python Lambda] --+--> [Odoo CRM]
|
+--> [AWS SES] --> [Notification Email]
```

---

## Prerequisites

Before you begin, ensure you have the following:

1.  **AWS Account:** With permissions to create IAM roles, Lambda functions, Function URLs, and manage SES.
2.  **Odoo Account:** An Odoo instance (cloud or self-hosted) with a user account that has permissions to create CRM Opportunities.
3.  **Verified SES Identity:** You must have a verified domain or email address in AWS SES to send emails from (e.g., `mohankrushiudyog.com`).
4.  **Node.js & npm:** Required to run the React frontend locally for testing.
5.  **Git:** To manage the source code.

---

## Setup and Deployment

This guide is broken into two parts: deploying the backend Lambda function and configuring the frontend application.

### Part 1: Backend Deployment (AWS Lambda)

#### Step 1: Verify an Identity in AWS SES
1.  In the AWS Console, navigate to the **Simple Email Service (SES)**.
2.  In the left menu, go to **Verified identities**.
3.  Click **Create identity**.
4.  Choose **Domain** (recommended) or **Email address**. For this project, you would verify `mohankrushiudyog.com`.
5.  Follow the on-screen instructions to add the required DNS records (for a domain) or click a verification link (for an email). The identity status must be "Verified".

#### Step 2: Grant Lambda Permissions for SES
1.  Navigate to **IAM** in the AWS Console.
2.  Find the execution role associated with your Lambda function (its name is usually `your-function-name-role-xxxxxx`).
3.  Click **Add permissions** -> **Attach policies**.
4.  Search for and select the `AmazonSESFullAccess` policy.
5.  Click **Attach policies**.

#### Step 3: Create the Lambda Function
1.  Navigate to the **Lambda** service.
2.  Click **Create function**.
3.  Select **Author from scratch**.
4.  **Function name:** `odoo-opportunity-creator`.
5.  **Runtime:** Choose **Python 3.11** (or a later version).
6.  **Architecture:** `x86_64`.
7.  Click **Create function**.

#### Step 4: Deploy the Code
1.  On your new function's page, scroll down to the **Code source** section.
2.  Open the `lambda_function.py` file.
3.  Delete the boilerplate code and paste the entire content of the Python script from the `lambda/` directory of this repository.
4.  Click the **Deploy** button.

#### Step 5: Configure Environment Variables
*This is the most critical step for security and functionality.*

1.  Go to the **Configuration** tab and select **Environment variables**.
2.  Click **Edit** and add the following keys and their corresponding values:
    * `ODOO_URL`: Your Odoo domain (e.g., `your-company.odoo.com`), without `https://`.
    * `ODOO_DB`: The name of your Odoo database.
    * `ODOO_USERNAME`: The Odoo user's login email.
    * `ODOO_PASSWORD`: The Odoo user's password or API Key.
    * `CLIENT_ID`: A secure, hard-to-guess string you create (e.g., a UUID).
    * `CLIENT_SECRET`: Another secure, hard-to-guess secret string.
    * `SENDER_EMAIL`: The verified SES email address (e.g., `info@mohankrushiudyog.com`).
    * `NOTIFICATION_EMAIL`: A comma-separated list of emails to receive notifications (e.g., `sales@example.com,manager@example.com`).
    * `AWS_REGION`: The AWS region where you use SES (e.g., `ap-south-1`).

3.  Click **Save**.

#### Step 6: Create and Configure the Function URL
1.  Still on the **Configuration** tab, select **Function URL**.
2.  Click **Create function URL**.
3.  **Auth type:** Choose **`NONE`**.
4.  **CORS:** Check the box to **Configure cross-origin resource sharing (CORS)**.
    * **Allow origin:** `*` (for testing) or your website's domain `https://www.your-domain.com` (for production).
    * **Allow methods:** `POST`, `OPTIONS`.
    * **Allow headers:** `Content-Type`, `x-client-id`, `x-client-secret`.
5.  Click **Save**.
6.  Copy the generated **Function URL**. You will need this for the frontend.

### Part 2: Frontend Configuration

1.  **Clone the Repository:**
    ```bash
    git clone clone https://github.com/Harsh1210/odoo-xmlrpc-opportunitity-creation-lambda-api.git
    cd odoo-xmlrpc-opportunitity-creation-lambda-api
    ```

2.  **Install Dependencies:**
    ```bash
    npm install
    ```

3.  **Configure `contact.tsx`:**
    Open `src/pages/contact.tsx` and update the constants at the top of the file:
    ```typescript
    const LAMBDA_FUNCTION_URL = 'PASTE_YOUR_FUNCTION_URL_HERE';
    const CLIENT_ID = 'PASTE_YOUR_CLIENT_ID_HERE';
    const CLIENT_SECRET = 'PASTE_YOUR_CLIENT_SECRET_HERE';
    ```

4.  **Run the Frontend Locally:**
    ```bash
    npm run dev
    ```
    This will start the development server, usually at `http://localhost:8080`.

---

## End-to-End Testing

1.  Open your browser and navigate to the local development URL.
2.  Go to the contact page.
3.  Open the browser's Developer Tools (F12 or Ctrl+Shift+I) and select the **Network** and **Console** tabs.
4.  Fill out and submit the form.
5.  **Check for Success:**
    * A "Success!" toast message should appear on the webpage.
    * The browser console should log the successful response from Lambda.
    * Log in to Odoo and confirm the new opportunity has been created in your CRM pipeline.
    * Check the inbox of the `NOTIFICATION_EMAIL` address(es) for the formatted HTML email.

---

## Troubleshooting

If you encounter issues, check the following common problems and solutions. The best place to start is always the **CloudWatch Logs** for your Lambda function.

| Error Message / Symptom                                        | Common Cause                                                                                             | Solution                                                                                                                                                                                                                                             |
| -------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `{"error": "Unauthorized"}` or `401 Unauthorized`              | The `x-client-id` or `x-client-secret` sent from the frontend do not match the Lambda environment variables. | Double-check that the `CLIENT_ID` and `CLIENT_SECRET` values in your frontend code are an exact match (including case) for the values in your Lambda function's **Environment variables**.                                                             |
| `{"error": "Method Not Allowed"}` or `405 Method Not Allowed`    | You are making a `GET` (or other) request to the endpoint, but it only accepts `POST`.                   | Ensure you are testing with a `POST` request. If you paste the URL in a browser, it sends a `GET` request. Use `curl`, Postman, or the provided sample `test.html` form. Check that your React `fetch` call explicitly specifies `method: 'POST'`. |
| `{"error": "Could not authenticate with Odoo: ..."}`           | One of the Odoo-related environment variables (`ODOO_URL`, `ODOO_DB`, `ODOO_USERNAME`, `ODOO_PASSWORD`) is incorrect. | Carefully verify all four Odoo environment variables in your Lambda configuration. Check for typos, extra spaces, or using `http://` in the URL. Ensure the user has the correct permissions in Odoo.                                                  |
| The request times out (e.g., `Status: timeout`)                | The Lambda function timeout is too short, or it lacks the necessary VPC/NAT Gateway configuration to access the internet. | In your Lambda's **Configuration -> General configuration**, increase the **Timeout** to at least **30 seconds**. If it still times out (especially on the SES call), your Lambda may need internet access via a NAT Gateway in your VPC. |
| `Failed to send SES notification email. Error: ...`            | The Lambda's execution role lacks SES permissions, or the `SENDER_EMAIL` is not a verified SES identity. | Ensure you've attached the `AmazonSESFullAccess` policy to your Lambda's IAM role. Verify that the email address in the `SENDER_EMAIL` variable has a "Verified" status in the AWS SES console.                                                      |
| CORS Error in browser console (e.g., `blocked by CORS policy`) | The CORS settings on the Lambda Function URL are incorrect or missing.                                     | Go to your Lambda's **Configuration -> Function URL**. Click **Edit**. Ensure CORS is enabled and that `Allow origin`, `Allow methods`, and `Allow headers` are configured correctly as described in the setup guide.                                |

---

## FAQ

**Q: Is it secure to put the `CLIENT_ID` and `CLIENT_SECRET` in the frontend JavaScript?**

**A:** While this setup is much more secure than exposing Odoo credentials, the Client ID and Secret are still visible in the client-side code. For production applications, you should use your build system (like Webpack or Vite) to inject these values from `.env` files. This makes it easier to manage different credentials for development and production without hardcoding them. For the highest security, you could implement a more advanced auth flow like OAuth or use AWS WAF to rate-limit and protect the endpoint.

**Q: How do I disable email notifications?**

**A:** Simply remove the `SENDER_EMAIL` and `NOTIFICATION_EMAIL` environment variables from your Lambda function's configuration. The code will see that they are missing and skip the email-sending step.

**Q: Can I use this function to create other records in Odoo, like Contacts or Helpdesk Tickets?**

**A:** Yes, absolutely. You would need to make two changes in `lambda_function.py`:
1.  **Model Name:** Change the model string from `'crm.lead'` to the target model's technical name (e.g., `'res.partner'` for contacts, `'helpdesk.ticket'` for tickets).
2.  **Payload Data:** In your frontend `contact.tsx` file, modify the `opportunityPayload` object to include the fields required by the new model.

**Q: Why not just call the Odoo XML-RPC API directly from the frontend?**

**A:** Calling Odoo directly from the browser would require exposing your Odoo username and password (or a master API key) to anyone who inspects the website's source code. This is a major security vulnerability. The Lambda function acts as a secure proxy, keeping all your credentials safe on the server side.

---

## Quick Test with a Sample Form

If you want to test the Lambda function without the full React setup, you can use this simple HTML file. Save it as `test.html`, update the configuration values, and open it in your browser.

```html
<!-- test.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Lambda Test Form</title>
    <style>
        body { font-family: sans-serif; max-width: 500px; margin: 2rem auto; }
        input, textarea, button { width: 100%; padding: 10px; margin-bottom: 10px; box-sizing: border-box; }
        #response { margin-top: 20px; padding: 10px; border-radius: 5px; }
        .success { background-color: #d4edda; color: #155724; }
        .error { background-color: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <h1>Odoo Test Form</h1>
    <form id="testForm">
        <input type="text" id="name" placeholder="Contact Name" value="HTML Form Tester" required><br>
        <input type="email" id="email" placeholder="Email" value="html.test@example.com" required><br>
        <textarea id="message" placeholder="Message">Test message from sample HTML form.</textarea><br>
        <button type="submit">Submit to Lambda</button>
    </form>
    <div id="response"></div>

    <script>
        // --- CONFIGURE THESE VALUES ---
        const LAMBDA_URL = 'YOUR_LAMBDA_FUNCTION_URL';
        const CLIENT_ID = 'YOUR_CLIENT_ID';
        const CLIENT_SECRET = 'YOUR_CLIENT_SECRET';

        document.getElementById('testForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const responseDiv = document.getElementById('response');
            responseDiv.textContent = 'Submitting...';
            responseDiv.className = '';

            const payload = {
                name: `Test from HTML: ${document.getElementById('name').value}`,
                contact_name: document.getElementById('name').value,
                email_from: document.getElementById('email').value,
                description: document.getElementById('message').value,
            };

            try {
                const response = await fetch(LAMBDA_URL, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'x-client-id': CLIENT_ID,
                        'x-client-secret': CLIENT_SECRET
                    },
                    body: JSON.stringify(payload)
                });
                
                const result = await response.json();

                if (!response.ok) {
                    throw new Error(result.error || 'Request failed');
                }
                
                responseDiv.textContent = `Success! Odoo ID: ${result.leadId}`;
                responseDiv.className = 'success';
            } catch (err) {
                responseDiv.textContent = `Error: ${err.message}`;
                responseDiv.className = 'error';
            }
        });
    </script>
</body>
</html>

