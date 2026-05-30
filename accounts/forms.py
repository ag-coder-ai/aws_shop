import re

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class SignupForm(forms.ModelForm):

    password = forms.CharField(
        widget=forms.PasswordInput
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput
    )

    class Meta:

        model = User

        fields = [
            "full_name",
            "email",
            "phone",
            "password",
        ]

    # ======================================
    # FULL NAME
    # ======================================

    def clean_full_name(self):

        name = self.cleaned_data["full_name"].strip()

        if len(name) < 3:

            raise ValidationError(
                "Enter valid full name."
            )

        return name

    # ======================================
    # PHONE
    # ======================================

    def clean_phone(self):

        phone = self.cleaned_data["phone"]

        phone = re.sub(r"\D", "", phone)

        if not re.match(
            r"^[6-9]\d{9}$",
            phone
        ):

            raise ValidationError(
                "Enter valid Indian mobile number."
            )

        if User.objects.filter(
            phone=phone
        ).exists():

            raise ValidationError(
                "Mobile number already exists."
            )

        return phone

    # ======================================
    # EMAIL
    # ======================================

    def clean_email(self):

        email = self.cleaned_data["email"].lower().strip()

        if User.objects.filter(
            email=email
        ).exists():

            raise ValidationError(
                "Email already registered."
            )

        blocked_domains = [

            "tempmail.com",
            "mailinator.com",
            "10minutemail.com",
            "yopmail.com"

        ]

        domain = email.split("@")[-1]

        if domain in blocked_domains:

            raise ValidationError(
                "Disposable emails are not allowed."
            )

        return email

    # ======================================
    # PASSWORD
    # ======================================

    def clean_password(self):

        password = self.cleaned_data["password"]

        if len(password) < 8:

            raise ValidationError(
                "Password must contain minimum 8 characters."
            )

        if not re.search(r"[A-Z]", password):

            raise ValidationError(
                "Password must contain uppercase letter."
            )

        if not re.search(r"[a-z]", password):

            raise ValidationError(
                "Password must contain lowercase letter."
            )

        if not re.search(r"\d", password):

            raise ValidationError(
                "Password must contain number."
            )

        if not re.search(
            r"[!@#$%^&*(),.?\":{}|<>]",
            password
        ):

            raise ValidationError(
                "Password must contain special character."
            )

        return password

    # ======================================
    # CONFIRM PASSWORD
    # ======================================

    def clean(self):

        cleaned_data = super().clean()

        password = cleaned_data.get("password")

        confirm = cleaned_data.get(
            "confirm_password"
        )

        if password != confirm:

            raise ValidationError(
                {
                    "confirm_password":
                    "Passwords do not match."
                }
            )

        return cleaned_data