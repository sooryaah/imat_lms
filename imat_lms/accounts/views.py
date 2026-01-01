# Admin-only view to list instructors
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import CustomUser
from .serializers import ProfileSerializer

class InstructorListView(APIView):
    """Admin only endpoint to list all instructors"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.is_admin:
            return Response({"error": "Only admins can view instructors."}, status=status.HTTP_403_FORBIDDEN)
        instructors = CustomUser.objects.filter(role='instructor')
        from .serializers import InstructorListSerializer
        serializer = InstructorListSerializer(instructors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import logout
from django.core.mail import send_mail
from django.conf import settings

import random
from .models import CustomUser, PasswordResetOTP
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    VerifyOTPSerializer,
    ResetPasswordSerializer,
    ProfileSerializer,
)
from rest_framework.permissions import IsAuthenticated
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ProfileSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                }
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()  
            logout(request)
            return Response({"message": "Logout successful"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)



class HomeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "message": f"Welcome {user.username}!",
            "email": user.email
        })


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            
            
            if not user.check_password(serializer.validated_data['oldpassword']):
                return Response(
                    {"oldpassword": "Old password is incorrect."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            
            user.set_password(serializer.validated_data['newpassword'])
            user.save()
            
            return Response(
                {"message": "Password changed successfully."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = CustomUser.objects.get(email=email)

            # Generate OTP
            code = f"{random.randint(1000, 9999)}"
            PasswordResetOTP.objects.create(user=user, code=code)

            # Email details
            subject = "Your Password Reset Code"
            from_email = settings.DEFAULT_FROM_EMAIL

            # FIXED INDENTATION (VERY IMPORTANT)
            html_content = f"""
            <div style="font-family: Arial, sans-serif; background: linear-gradient(135deg, #c8001a 0%, #2d0a0a 100%); padding: 20px 0;">
                <div style="
                    max-width: 380px;
                    margin: 20px auto;
                    background: rgba(30,0,0,0.65);
                    padding: 24px 20px;
                    border-radius: 22px;
                    box-shadow: 0 4px 18px rgba(0,0,0,0.18);
                    text-align: center;
                ">
                    <h2 style="color: #fff; font-size: 1.6em; margin-bottom: 4px; font-weight: 600;">
                        imat <span style='color: #e74c3c;'>global</span>
                    </h2>
                    <div style="color: #fff; font-size: 0.9em; margin-bottom: 12px;">
                        Consultants &amp; Training
                    </div>
                    <div style="height: 1px; background: #fff2; margin: 14px 0;"></div>
                    <p style="color: #fff; font-size: 1em; margin: 6px 0;">
                        Hello <strong>{user.full_name}</strong>,
                    </p>
                    <p style="color: #fff; font-size: 0.95em; margin: 6px 0;">
                        Use the verification code below to reset your password:
                    </p>
                    <div style="
                        font-size: 2em;
                        font-weight: bold;
                        letter-spacing: 10px;
                        padding: 16px;
                        background: rgba(255,255,255,0.08);
                        border-radius: 10px;
                        margin: 16px auto;
                        color: #fff;
                        border: 2px dashed #fff3;
                        width: 65%;
                    ">
                        {code}
                    </div>
                    <p style="font-size: 0.9em; color: #fff; margin: 6px 0;">
                        This code expires in <strong>15 minutes</strong>.
                    </p>
                    <p style="color: #fff; font-size: 0.85em; margin-top: 10px;">
                        If you did not request this, you may ignore it.
                    </p>
                    <a href="#" style="
                        display: inline-block;
                        background: linear-gradient(90deg, #c8001a 0%, #2d0a0a 100%);
                        color: #fff;
                        padding: 10px 26px;
                        text-decoration: none;
                        border-radius: 8px;
                        font-weight: bold;
                        font-size: 1em;
                        margin-top: 14px;
                    ">Reset Password</a>
                    <div style="font-size:0.85em; color:#fff8; margin-top: 14px;">
                        Thank you!<br>imat global team
                    </div>
                </div>
            </div>
            """

            # Email send code
            email_message = EmailMultiAlternatives(
                subject=subject,
                body="Your OTP is " + code,  # fallback plain text
                from_email=from_email,
                to=[email]
            )
            email_message.attach_alternative(html_content, "text/html")
            email_message.send()

            return Response({"message": "Verification code sent to email"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
          
            return Response({"message": "Code verified. Proceed to reset password."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            otp = serializer.validated_data['otp']

          
            user.set_password(serializer.validated_data['newpassword'])
            user.save()

        
        
            otp.mark_used()

            return Response({"message": "Password has been reset. You may now login."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateTeacherView(APIView):
    """Admin only endpoint to create teacher/instructor users"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Check if user is admin
        if not request.user.is_admin:
            return Response(
                {"error": "Only admins can create teachers."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Set role to instructor
            user.role = 'instructor'
            user.save()
            return Response({
                "message": "Teacher created successfully",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





