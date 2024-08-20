from django.core.mail import send_mail
from django.conf import settings

def send_email_to_client(email, token):
    subject = 'Reset Your Password'
    message = f'Please click on the following link to reset your password: http://127.0.0.1:8000/ChangePassword/{token}/'
    email_from = settings.DEFAULT_FROM_EMAIL  # Using DEFAULT_FROM_EMAIL is better practice
    recipient_list = [email]
    
    try:
        send_mail(subject, message, email_from, recipient_list)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
