from rest_framework.throttling import UserRateThrottle

# Ensure to give proper configuration during production when using a load balancer

class OTPRequestThrottle(UserRateThrottle):
    scope = "otp_request"
    rate = "10/hour"


class LoginAttemptThrottle(UserRateThrottle):
    scope = "login_attempt"
    rate = "10/10min"