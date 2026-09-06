from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from profiles.models import ClientHealthProfile, ClientProfile, RndProfile

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "role",
            "phone", "profile_photo", "is_active", "created_at",
        ]
        read_only_fields = fields


class RegisterClientSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    sex = serializers.ChoiceField(choices=ClientProfile.Sex.choices, required=False, allow_null=True)
    primary_health_concern = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        health_concern = validated_data.pop("primary_health_concern", "")
        date_of_birth = validated_data.pop("date_of_birth", None)
        sex = validated_data.pop("sex", None)

        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            role=User.Role.CLIENT,
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )
        ClientProfile.objects.create(user=user, date_of_birth=date_of_birth, sex=sex)
        ClientHealthProfile.objects.create(
            user=user,
            health_goals=[health_concern] if health_concern else None,
        )
        return user


class RegisterRndSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    prc_license_number = serializers.CharField(max_length=50)
    specialization = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate_prc_license_number(self, value):
        if RndProfile.objects.filter(prc_license_number=value).exists():
            raise serializers.ValidationError("This PRC license number is already registered.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            role=User.Role.RND,
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )
        RndProfile.objects.create(
            user=user,
            prc_license_number=validated_data["prc_license_number"],
            specialization=validated_data.get("specialization", ""),
            is_verified=False,
        )
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        # Deliberately does NOT raise if the email doesn't exist — the view
        # always returns the same generic success response either way, so
        # this endpoint can't be used to enumerate registered emails.
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])


class NutriMatchTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Adds role/name claims to the JWT and returns the user alongside the tokens."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["full_name"] = user.full_name
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data
