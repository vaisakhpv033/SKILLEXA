# push_notification.py
import os
import threading
import firebase_admin
from firebase_admin import credentials, messaging
from decouple import config
from django.contrib.auth import get_user_model
from accounts.models import FCMToken, Notification

User = get_user_model()

# Firebase App instance (singleton)
_firebase_app = None

def get_firebase_app():
    """
    Initialize Firebase Admin SDK if not already initialized
    """
    global _firebase_app
    
    if _firebase_app is None:
        try:
            cred_path = config('GOOGLE_CLOUD_CREDENTIALS')
            if not os.path.exists(cred_path):
                raise FileNotFoundError(f"Firebase credentials not found at: {cred_path}")
            
            cred = credentials.Certificate(cred_path)
            _firebase_app = firebase_admin.initialize_app(cred)
        except Exception as e:
            print(f"Firebase initialization failed: {str(e)}")
            raise
    
    return _firebase_app

def send_push_notification(user, title, body, data={}, is_async=True):
    def _send():
        try:
            app = get_firebase_app()

            tokens = list(FCMToken.objects.filter(user=user).values_list('token', flat=True))
            
            if not tokens:
                print(f"No FCM tokens found for user: {user.id}")
                return

            notifications=messaging.Notification(
                    title=title,
                    body=body,
                    **data
            )
            message = messaging.MulticastMessage(
                notification=notifications,
                data={k: str(v) for k, v in (data or {}).items()},
                tokens=tokens,
            )

            Notification.objects.create(
                user = user,
                notification = {
                    "title": title,
                    "body": body, 
                    **data
                }
            )

        
            response = messaging.send_each_for_multicast(message, app=app)
            
            

            print(f"Sent to {response.success_count} devices")

        except Exception as e:
            print(f"Notification error: {str(e)}")


    if is_async:
        thread = threading.Thread(target=_send, daemon=True)
        thread.start()
    else:
        _send()