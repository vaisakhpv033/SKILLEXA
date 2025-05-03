from celery import shared_task
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from skillexa.settings import DEFAULT_FROM_EMAIL
from accounts.models import  Notification
from accounts.utils import send_fcm_notification
import logging

logger = logging.getLogger(__name__)

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



@shared_task
def send_push_notification_task(user_id, title, body, data=None):
    if data is None:
        data = {}
    User = get_user_model()

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.warning(f"User with ID {user_id} not found")
        return
    
    logger.warning(f"user {user_id} title{title} body: {body}, data: {data}")
    # Always save the notification to DB
    try:
        Notification.objects.create(
            user=user,
            notification={
                "title": title,
                "body": body,
                **data
            }
        )
    except Exception as e:
        logger.exception(f"Failed to save notification for user {user_id}")


    # Send FCM notification
    send_fcm_notification(user, title, body, data)

