from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Profile
from pathlib import Path
from django.contrib.auth.forms import AuthenticationForm


def validate_avatar_upload(avatar):
    formats = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG",}

    extension = Path(avatar.name).suffix.lower()

    if extension not in formats or avatar.image.format != formats[extension]:
        raise ValidationError(
            "Upload a JPEG or PNG image with the matching extension."
        )

    if avatar.size > 2_000_000:
        raise ValidationError(
            "The avatar must be 2 MB or smaller."
        )

class LoginForm(AuthenticationForm):
    pass

class RegisterForm(forms.ModelForm):
    username = forms.CharField(max_length=50)
    email = forms.EmailField(max_length=254)
    nick = forms.CharField(max_length=50)
    avatar = forms.ImageField(required=False)

    password = forms.CharField(
        widget=forms.PasswordInput,
        strip=False,
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput,
        strip=False,
    )

    class Meta:
        model = User
        fields = ("username", "email")

    def clean_nick(self):
        nick = self.cleaned_data["nick"]

        if Profile.objects.filter(nick=nick).exists():
            raise ValidationError("This nickname is already taken.")

        return nick
    
    def clean_avatar(self):
        avatar = self.cleaned_data["avatar"]

        if avatar:
            validate_avatar_upload(avatar)

        return avatar

    def clean(self):
        data = super().clean()

        password = data.get("password")
        password2 = data.get("password2")

        if password and password2 and password != password2:
            self.add_error(
                "password2",
                "Passwords do not match.",
            )

        if password:
            candidate = User(
                username=data.get("username", ""),
                email=data.get("email", ""),
            )

            try:
                validate_password(password, user=candidate)
            except ValidationError as error:
                self.add_error("password", error)

        return data

    @transaction.atomic
    def save(self):
        data = self.cleaned_data

        user = User.objects.create_user(
            username=data["username"],
            email=data["email"],
            password=data["password"],
        )

        Profile.objects.create(
            user=user,
            nick=data["nick"], avatar=data["avatar"],
        )

        return user


class ProfileForm(forms.ModelForm):
    email = forms.EmailField(max_length=254)
    nick = forms.CharField(max_length=50)
    avatar = forms.ImageField(required=False)


    class Meta:
        model = Profile
        fields = ("email", "nick", "avatar")


    def __init__(self, user, *args, **kwargs):
        self.user = user

        profile = getattr(user, "profile", None)
        if profile is None:
            profile = Profile(user=user)

        super().__init__(
            *args,
            instance=profile,
            initial={"email": user.email},
            **kwargs,
        )



    def clean_avatar(self):
        avatar = self.cleaned_data["avatar"]

        if self.files.get(self.add_prefix("avatar")):
            validate_avatar_upload(avatar)

        return avatar



    @transaction.atomic
    def save(self):
        profile = super().save()

        self.user.email = self.cleaned_data["email"]
        self.user.save(update_fields=["email"])

        return profile

