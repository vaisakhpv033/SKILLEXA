from celery import shared_task
from django.core.mail import send_mail

from skillexa.settings import DEFAULT_FROM_EMAIL


@shared_task
def send_otp_email(email, otp):
    subject = "Your OTP Code"
    message = f"Your OTP for account verification is: {otp}"
    sender_email = DEFAULT_FROM_EMAIL
    recipient_list = [email]

    send_mail(subject, message, sender_email, recipient_list)
    return f"OTP sent to {email}"


@shared_task
def send_forgot_password_otp_email(email, otp):
    subject = "Your OTP Code For Password Resetting"
    message = f"Your OTP for password resetting is: {otp}"
    sender_email = DEFAULT_FROM_EMAIL
    recipient_list = [email]

    send_mail(subject, message, sender_email, recipient_list)


@shared_task
def send_email(email, subject, message):
    sender_email = DEFAULT_FROM_EMAIL
    recipient_list = [email]

    send_mail(subject, message, sender_email, recipient_list)
