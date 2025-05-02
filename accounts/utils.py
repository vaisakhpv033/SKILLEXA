import os
import logging
from firebase_admin import credentials, messaging, initialize_app
from decouple import config
from django.contrib.auth import get_user_model
from accounts.models import FCMToken, Notification

logger = logging.getLogger(__name__)
User = get_user_model()

# Firebase App instance (singleton)
_firebase_app = None

def get_firebase_app():
    global _firebase_app
    if _firebase_app is None:
        try:
            cred_path = config('GOOGLE_CLOUD_CREDENTIALS')
            if not os.path.exists(cred_path):
                raise FileNotFoundError(f"Firebase credentials not found at: {cred_path}")
            
            cred = credentials.Certificate(cred_path)
            _firebase_app = initialize_app(cred)
        except Exception as e:
            logger.exception("Firebase initialization failed")
            raise
    return _firebase_app

def send_push_notification(user, title, body, data={}, is_async=True):
    def _send():
        try:
            app = get_firebase_app()
            tokens = list(FCMToken.objects.filter(user=user).values_list('token', flat=True))

            if not tokens:
                logger.info(f"No FCM tokens found for user {user.id}")
                return

            notification = messaging.Notification(
                title=title,
                body=body
            )

            message = messaging.MulticastMessage(
                notification=notification,
                data={k: str(v) for k, v in data.items()},
                tokens=tokens
            )

            response = messaging.send_each_for_multicast(message, app=app)

            # Cleanup invalid tokens
            invalid_tokens = [
                tokens[i]
                for i, resp in enumerate(response.responses)
                if not resp.success and isinstance(resp.exception, messaging.UnregisteredError)
            ]
            if invalid_tokens:
                FCMToken.objects.filter(user=user, token__in=invalid_tokens).delete()
                logger.info(f"Removed {len(invalid_tokens)} invalid tokens for user {user.id}")

            # Save the notification regardless of push success
            Notification.objects.create(
                user=user,
                notification={
                    "title": title,
                    "body": body,
                    **data
                }
            )
            logger.info(f"Notification sent to {response.success_count} devices for user {user.id}")

        except Exception as e:
            logger.exception("Failed to send push notification")

    if is_async:
        from .tasks import send_push_notification_task
        send_push_notification_task.delay(user.id, title, body, data)
    else:
        _send()
