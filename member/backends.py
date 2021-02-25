import hashlib
from django.contrib.auth import get_user_model

UserModel = get_user_model()

class MemberBackend:
    def authenticate(self, email=None, password=None):
        try:
            user = UserModel.objects.get(email=email)
            if user.check_password(password):
                return user
            else:
                return None

        except UserModel.DoesNotExist:
            return None

    def user_can_authenticate(self, user):
        is_active = getattr(user, 'is_active', None)
        return is_active or is_active is None

    def get_user(self, user_id):
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None