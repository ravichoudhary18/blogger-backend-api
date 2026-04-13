from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .validators import CustomPasswordValidator
from .models import UserProfile
from django.db import transaction

COUNTRY_MOBILE_LENGTH_MAP = {
    "+91": 10,
    "+1": 10,
    "+44": 10,
}


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True, validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        write_only=True, required=True, validators=[CustomPasswordValidator()], style={"input_type": "password"}
    )
    confirm_password = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )
    country_code = serializers.CharField(required=True, write_only=True)
    mobile_number = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = User
        fields = (
            "username",
            "password",
            "confirm_password",
            "email",
            "first_name",
            "last_name",
            "country_code",
            "mobile_number",
        )
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
            
        country_code = attrs.get("country_code")
        mobile_number = attrs.get("mobile_number")
        
        if country_code not in COUNTRY_MOBILE_LENGTH_MAP:
            raise serializers.ValidationError(
                {"country_code": f"Unsupported country code. Supported codes: {', '.join(COUNTRY_MOBILE_LENGTH_MAP.keys())}"}
            )
            
        expected_length = COUNTRY_MOBILE_LENGTH_MAP[country_code]
        if not mobile_number.isdigit():
            raise serializers.ValidationError(
                {"mobile_number": "Mobile number must contain only digits."}
            )
            
        if mobile_number.startswith('0'):
            raise serializers.ValidationError(
                {"mobile_number": "Mobile number must not start with 0."}
            )
            
        if len(mobile_number) != expected_length:
            raise serializers.ValidationError(
                {"mobile_number": f"Mobile number for {country_code} must be {expected_length} digits long."}
            )
            
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        country_code = validated_data.pop("country_code")
        mobile_number = validated_data.pop("mobile_number")
        validated_data.pop("confirm_password")
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )
        UserProfile.objects.create(
            user=user,
            country_code=country_code,
            mobile_number=mobile_number
        )
        return user


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    username = serializers.CharField(
        error_messages={
            "blank": "Please provide your username or email.",
            "required": "Username or email field is missing.",
        }
    )
    password = serializers.CharField(
        error_messages={
            "blank": "Please provide your password.",
            "required": "Password field is missing.",
        }
    )

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token["username"] = user.username
        token["email"] = user.email
        return token

    def validate(self, attrs):
        username_or_email = attrs.get("username")

        # Explicit check: if @ is in input, it's an email, else it's a username
        if "@" in username_or_email:
            user = User.objects.filter(email=username_or_email).first()
        else:
            user = User.objects.filter(username=username_or_email).first()

        if user:
            # Update the username in attrs to the actual username for authentication
            attrs["username"] = user.username

        data = super().validate(attrs)

        # Add user information to the response
        data["user"] = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
        }

        return data


class UserBasicInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email")
