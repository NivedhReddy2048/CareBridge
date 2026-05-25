from rest_framework_simplejwt.views import TokenObtainPairView
from api.v1.serializers.auth_serializers import CustomTokenObtainPairSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Takes a set of user credentials and returns an access and refresh JSON web token
    with custom claims like role and username.
    """
    serializer_class = CustomTokenObtainPairSerializer
