from functools import wraps
from django.http import JsonResponse
import firebase_admin
from firebase_admin import auth

def firebase_auth_required(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'No token provided'}, status=401)
        
        token = auth_header.split('Bearer ')[1].strip()

        print(token)
        try:
            # Verify the Firebase token
            decoded_token = auth.verify_id_token(token)
            request.firebase_user = decoded_token  # Attach firebase user info to request
            return view_func(request, *args, **kwargs)
        except Exception as e:
            print(e)
            return JsonResponse({'error': 'Invalid token, ' + str(e)}, status=401)
            
    return wrapped_view 