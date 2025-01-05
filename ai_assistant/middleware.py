import firebase_admin
from firebase_admin import auth
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.utils.functional import SimpleLazyObject
from django.contrib.auth import login

User = get_user_model()

def get_user_from_firebase(request):
    # Get the ID token from the Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return AnonymousUser()

    token = auth_header.split('Bearer ')[1]
    try:
        # Verify the Firebase token
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token['uid']
        email = decoded_token.get('email', '')
        
        # Get or create user
        user, created = User.objects.get_or_create(
            username=uid,
            defaults={
                'email': email,
                # Add other fields as needed
            }
        )
        
        # Optionally login the user
        login(request, user)
        return user
    except Exception as e:
        print(f"Firebase auth error: {e}")
        return AnonymousUser()

class FirebaseAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.user = SimpleLazyObject(lambda: get_user_from_firebase(request))
        return self.get_response(request) 