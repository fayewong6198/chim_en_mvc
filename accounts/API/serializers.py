from ..models import User
from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework.response import Response


class UserSerializer(serializers.ModelSerializer):
    addresses = serializers.StringRelatedField(many=True)
    favorites = serializers.StringRelatedField(many=True)
    orders = serializers.StringRelatedField(many=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name',
                  'last_name', 'gender', 'date_of_birth', 'addresses', 'favorites', 'orders']

# Register Serializer


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'is_staff')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):

        user = User.objects.create_user(
            validated_data['username'], validated_data['email'], validated_data['password'])
        print(validated_data)
        if 'is_staff' in validated_data:
            print("DIT ME MAY")
            user.is_staff = validated_data['is_staff']
            print(user.is_staff)

        return user

# Login Serializer


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):

        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Incorrect Credentials")
