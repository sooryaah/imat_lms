from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password

class EmailOrSuperuserUsernameBackend(BaseBackend):
    """
    Allows superusers to log in with username, and regular users with email.
    """
    def authenticate(self, request, username=None, email=None, password=None, **kwargs):
        UserModel = get_user_model()
        user = None
        # Try superuser login with username
        if username:
            try:
                user = UserModel.objects.get(username=username)
                if user.is_superuser and user.check_password(password):
                    return user
            except UserModel.DoesNotExist:
                pass
        # Try regular user login with email
        if email:
            try:
                user = UserModel.objects.get(email=email)
                if user.check_password(password):
                    return user
            except UserModel.DoesNotExist:
                pass
        return None
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class SuperuserUsernameBackend(ModelBackend):
    """
    Allows superusers to log in using username and password.
    Regular users must use email and password.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        import logging
        logger = logging.getLogger("django.auth")
        UserModel = get_user_model()
        logger.debug(f"SuperuserUsernameBackend: Trying username={username}")
        try:
            user = UserModel.objects.get(username=username)
            logger.debug(f"Found user: {user.username}, is_superuser={user.is_superuser}, is_active={user.is_active}")
        except UserModel.DoesNotExist:
            logger.debug(f"User with username={username} does not exist.")
            return None
        if user.is_superuser and user.check_password(password):
            logger.debug(f"Superuser credentials valid for username={username}")
            return user
        logger.debug(f"Superuser credentials invalid for username={username}")
        return None
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class EmailOrUsernameAdminBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        user = None
        # Try username
        if username is not None:
            try:
                user = UserModel.objects.get(username=username)
            except UserModel.DoesNotExist:
                pass
        # Try email if not found by username
        if user is None and username is not None:
            try:
                user = UserModel.objects.get(email=username)
            except UserModel.DoesNotExist:
                return None
        if user and (user.is_superuser or user.is_staff):
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        return None
