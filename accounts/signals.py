from django.db.models.signals import post_save 
from django.dispatch import receiver
from django.contrib.auth import get_user_model 
from wallet.models import Wallet 


user = get_user_model() 

@receiver(post_save, sender=user)
def create_wallet(sender, instance, created, **kwargs):
    """
    create a wallet automatically when a new user is created 
    """
    if created:
        Wallet.objects.create(user=instance)
        print(f"Wallet created for user: {instance.email}")