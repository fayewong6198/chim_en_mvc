from ..models import User
from .serializers import UserSerializer, RegisterSerializer, LoginSerializer, PermissionSerializer
from rest_framework import viewsets, generics
from rest_framework import permissions
from rest_framework.response import Response
from knox.models import AuthToken
from django.shortcuts import get_object_or_404
from ecom.pagination import StandardResultsSetPagination, PaginationHandlerMixin, LargeResultsSetPagination
from rest_framework.decorators import action
from django.contrib.auth.models import Permission

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.http import HttpResponse
import json


class PermissionViewSet(viewsets.ModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [permissions.AllowAny]


def user_permissions(request, pk):
    if (request.method == 'POST'):
        user = get_object_or_404(User, pk=pk)
        print("ccc")
        print(request.POST['user_permissions'], "cc")
        print("cc")
        ids = []
        for permission in request.POST['user_permissions']:
            ids.append(permission.id)
        print("ids")
        print(ids)
        permissions = Permission.objects.filter(id__in=ids)
        print("ahihi")
        print(permissions)
        user.user_permissions.set(permissions)
        user.save()

    return Response({'user': user})


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=True, methods=['POST'])
    def set_permissions(self, request, pk=None):
        user = self.get_object()
        ids = []
        for permission in request.data['user_permissions']:
            ids.append(permission['id'])

        permissions = Permission.objects.filter(id__in=ids)
        print("ahihi")
        print(permissions)
        user.user_permissions.set(permissions)
        user.save()
        return Response({'user': UserSerializer(user, context=self.get_serializer_context()).data})


class RegisterAPI(generics.GenericAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid() == False:

            return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        user = serializer.save()
        return Response({
            'user': UserSerializer(user, context=self.get_serializer_context()).data,
            'token': AuthToken.objects.create(user)[1]
        })


# Login API
class LoginAPI(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):

        print(request.data)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        return Response({
            'user': UserSerializer(user, context=self.get_serializer_context()).data,
            'token': AuthToken.objects.create(user)[1]
        })

# Get User API


class UserAPI(generics.RetrieveAPIView):
    permission_classes = [
        permissions.IsAuthenticated
    ]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
