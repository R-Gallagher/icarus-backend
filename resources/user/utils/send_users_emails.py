from datetime import timedelta
from os import environ

from app import app
from flask_jwt_extended import (create_access_token, fresh_jwt_required,
                                get_jwt_identity)
from python_http_client import exceptions
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (Content, Email, Mail, Personalization,
                                   Substitution, To)

# add error handling
def send_confirmation_email(to: str, verification_code: str):
    with app.app_context():

        message = Mail(
            from_email='support@icarusmed.com',
            to_emails=to)
        message.dynamic_template_data = {
            'verificationToken': verification_code,
        }
        message.template_id = environ.get("CONFIRMATION_EMAIL_TEMPLATE_ID")
        # try:
        # to the user
        sendgrid_client = SendGridAPIClient(environ.get('SENDGRID_API_KEY'))
        sendgrid_client.send(message)
        
        # to us about the user
        to_us_message = Mail(
        from_email='welcome@icarusmed.com',
        to_emails='support@icarusmed.com',
        subject='A New User Has Registered',
        html_content="Their email is {}".format(to))

        try:
            sendgrid_client.send(to_us_message)
        except Exception as e:
            print(e)


# add error handling
def send_password_reset_email(to: str, reset_token: str):
    with app.app_context():

        message = Mail(
            from_email='support@icarusmed.com',
            to_emails=to)
        message.dynamic_template_data = {
            'resetToken': reset_token,
        }
        message.template_id = environ.get('FORGOT_PASSWORD_EMAIL_TEMPLATE_ID')
        try:
            sendgrid_client = SendGridAPIClient(environ.get('SENDGRID_API_KEY'))
            response = sendgrid_client.send(message)
        except Exception as e:
            print(e)


# add error handling
def send_admin_confirmation_email_to_providers(providers: object, admin: object ):
    with app.app_context():

        for provider in providers:
            # which admin uuid is this for? we need a body element identify this
            accept_token = create_access_token(
                identity=provider.uuid, fresh=True, expires_delta=False)

            # why cant we just sent the email to the email list?
            # Because transactional templates dont support substitution for a single To() class
            message = Mail(
                from_email=Email('support@icarusmed.com'),
                to_emails=provider.email,
                subject='Icarus Admin Request',
                is_multiple=True)
            message.template_id = environ.get("ADMIN_CONFIRMATION_TO_PROVIDERS_TEMPLATE_ID")

            message.dynamic_template_data = {
                    'adminName': admin.name,
                    'adminEmail': admin.email,
                    'adminUUID': admin.uuid,
                    'providerName': provider.name,
                    'acceptToken': accept_token,
                    }

            try:
                sg = SendGridAPIClient(environ.get('SENDGRID_API_KEY'))
                response = sg.send(message)
            except Exception as e:
                print(e)
