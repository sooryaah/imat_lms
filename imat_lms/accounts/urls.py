from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('home/',views.HomeView.as_view(), name='home'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot-password'),
    path('verify-otp/', views.VerifyOTPView.as_view(), name='verify-otp'),
    path('reset-password/', views.ResetPasswordView.as_view(), name='reset-password'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('create-teacher/', views.CreateTeacherView.as_view(), name='create-teacher'),
    path('instructors/', views.InstructorListView.as_view(), name='instructor-list'),
]
