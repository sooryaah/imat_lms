from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser
from .models import PasswordResetOTP
from django.utils import timezone
import random

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'password']

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class InstructorListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'full_name', 'date_of_birth', 'gender', 'course_name', 'joining_month', 'mobile_number', 'profile_image']

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        user = None
        # Use the custom backend directly
        from accounts.backends import EmailOrSuperuserUsernameBackend
        backend = EmailOrSuperuserUsernameBackend()
        if username:
            user = backend.authenticate(self.context.get('request'), username=username, password=password)
        if not user and email:
            user = backend.authenticate(self.context.get('request'), email=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        data['user'] = user
        return data


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

  
    def validate_email(self, value):
        return value


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=10)

    def validate(self, data):
        try:
            user = CustomUser.objects.get(email=data['email'])
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError({"email": "No user found for this email."})

      
        otp_qs = PasswordResetOTP.objects.filter(user=user, code=data['code'], is_used=False).order_by('-created_at')
        if not otp_qs.exists():
            raise serializers.ValidationError({"code": "Invalid or used verification code."})
        otp = otp_qs.first()
        if otp.is_expired():
            raise serializers.ValidationError({"code": "Verification code has expired."})

        data['user'] = user
        data['otp'] = otp
        return data


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=10)
    newpassword = serializers.CharField(write_only=True, required=True)
    confirmpassword = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        if data['newpassword'] != data['confirmpassword']:
            raise serializers.ValidationError({"confirmpassword": "New password and confirm password do not match."})

        try:
            user = CustomUser.objects.get(email=data['email'])
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError({"email": "No user found for this email."})

        otp_qs = PasswordResetOTP.objects.filter(user=user, code=data['code'], is_used=False).order_by('-created_at')
        if not otp_qs.exists():
            raise serializers.ValidationError({"code": "Invalid or used verification code."})
        otp = otp_qs.first()
        if otp.is_expired():
            raise serializers.ValidationError({"code": "Verification code has expired."})

        data['user'] = user
        data['otp'] = otp
        return data


class ChangePasswordSerializer(serializers.Serializer):
    oldpassword = serializers.CharField(write_only=True, required=True)
    newpassword = serializers.CharField(write_only=True, required=True)
    confirmpassword = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        if data['newpassword'] != data['confirmpassword']:
            raise serializers.ValidationError(
                {"confirmpassword": "New password and confirm password do not match."}
            )
        
        if data['oldpassword'] == data['newpassword']:
            raise serializers.ValidationError(
                {"newpassword": "New password cannot be the same as old password."}
            )
        
        return data
    
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'email',
            'full_name',
            'date_of_birth',
            'gender',
            'course_name',
            'joining_month',
            'mobile_number',
            'profile_image', 
        ]
        read_only_fields = ['email']



        