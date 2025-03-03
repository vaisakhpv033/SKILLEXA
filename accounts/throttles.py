from rest_framework.throttling import UserRateThrottle

# Ensure to give proper configuration during production when using a load balancer

class OTPRequestThrottle(UserRateThrottle):
    scope = "otp_request"


class LoginAttemptThrottle(UserRateThrottle):
    scope = "login_attempt"