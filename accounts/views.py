from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import LoginSerializer, UserSerializer, UserCreateSerializer
from .models import User


def get_tokens(user):
    refresh = RefreshToken.for_user(user)
    refresh["role"]  = user.role
    refresh["name"]  = user.name
    refresh["email"] = user.email
    return {
        "refresh": str(refresh),
        "access":  str(refresh.access_token),
    }


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            errors = serializer.errors.get("non_field_errors", ["Invalid request."])
            locked = serializer.errors.get("locked", False)
            return Response(
                {"error": errors[0] if errors else "Invalid request.", "locked": bool(locked)},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user   = serializer.validated_data["user"]
        tokens = get_tokens(user)
        return Response({
            "tokens": tokens,
            "user": UserSerializer(user).data,
        }, status=status.HTTP_200_OK)


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class UserListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != "admin":
            return Response({"error": "Forbidden."}, status=403)
        users = User.objects.all()
        return Response(UserSerializer(users, many=True).data)

    def post(self, request):
        if request.user.role != "admin":
            return Response({"error": "Forbidden."}, status=403)
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            return None

    def patch(self, request, pk):
        if request.user.role != "admin":
            return Response({"error": "Forbidden."}, status=403)
        user = self.get_object(pk)
        if not user:
            return Response({"error": "User not found."}, status=404)
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        if request.user.role != "admin":
            return Response({"error": "Forbidden."}, status=403)
        user = self.get_object(pk)
        if not user:
            return Response({"error": "User not found."}, status=404)
        user.is_active = False
        user.save(update_fields=["is_active"])
        return Response({"message": "User deactivated."}, status=200)
