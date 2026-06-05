from django.contrib.auth import (
    get_user_model,
    login
)


from django.views import View

import re


User = get_user_model()

def check_email(request):

    email = request.GET.get("email", "").strip().lower()

    if not email:
        return JsonResponse({"available": False})

    exists = User.objects.filter(email=email).exists()

    return JsonResponse({
        "available": not exists
    })



class SignupView(View):

    def get(self, request):

        return render(
            request,
            "accounts/signup.html"
        )

    def post(self, request):

        full_name = request.POST.get(
            "full_name",
            ""
        ).strip()

        email = request.POST.get(
            "email",
            ""
        ).strip().lower()

        phone = request.POST.get(
            "phone",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        confirm_password = request.POST.get(
            "confirm_password",
            ""
        )

        # =====================================
        # VALIDATIONS
        # =====================================

        if len(full_name) < 3:

            messages.error(
                request,
                "Enter valid full name."
            )

            return redirect("signup")

        if not re.match(
            r"^[A-Za-z\s]+$",
            full_name
        ):

            messages.error(
                request,
                "Full name can contain only letters."
            )

            return redirect("signup")

        email_regex = (
            r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
        )

        if not re.match(
            email_regex,
            email
        ):

            messages.error(
                request,
                "Enter valid email address."
            )

            return redirect("signup")

        if User.objects.filter(
            email=email
        ).exists():

            messages.error(
                request,
                "Email already registered."
            )

            return redirect("signup")

        if not re.match(
            r"^[6-9]\d{9}$",
            phone
        ):

            messages.error(
                request,
                "Enter valid mobile number."
            )

            return redirect("signup")

        if User.objects.filter(
            phone=phone
        ).exists():

            messages.error(
                request,
                "Phone number already exists."
            )

            return redirect("signup")

        if len(password) < 8:

            messages.error(
                request,
                "Password must contain at least 8 characters."
            )

            return redirect("signup")

        if password != confirm_password:

            messages.error(
                request,
                "Passwords do not match."
            )

            return redirect("signup")

        # =====================================
        # CREATE USER
        # =====================================

        user = User.objects.create_user(

            email=email,
            phone=phone,
            password=password,
            full_name=full_name

        )

        # =====================================
        # AUTO LOGIN
        # =====================================

        login(
            request,
            user
        )

        messages.success(
            request,
            "Account created successfully."
        )

        return redirect("home")

from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.views import redirect_to_login
from django.contrib import messages

from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

User = get_user_model()


class LoginView(View):

    template_name = "accounts/login.html"

    # =========================
    # GET
    # =========================

    def get(self, request):

        # ALREADY LOGGED IN
        if request.user.is_authenticated:

            return redirect("home")

        return render(
            request,
            self.template_name
        )

    # =========================
    # POST
    # =========================

    def post(self, request):

        is_ajax = request.headers.get(
            "X-Requested-With"
        ) == "XMLHttpRequest"

        email = request.POST.get(
            "email",
            ""
        ).strip().lower()

        password = request.POST.get(
            "password",
            ""
        ).strip()

        remember = request.POST.get("remember")

        # =========================
        # VALIDATION
        # =========================

        if not email or not password:

            message = "Email and password are required."

            if is_ajax:

                return JsonResponse({
                    "success": False,
                    "message": message
                }, status=400)

            messages.error(
                request,
                message
            )

            return redirect("login")

        # =========================
        # EMAIL VALIDATION
        # =========================

        if "@" not in email:

            message = "Please enter a valid email address."

            if is_ajax:

                return JsonResponse({
                    "success": False,
                    "message": message
                }, status=400)

            messages.error(
                request,
                message
            )

            return redirect("login")

        # =========================
        # AUTHENTICATION
        # =========================

        user = authenticate(
            request,
            username=email,
            password=password
        )

        if user is None:

            message = "Invalid email or password."

            if is_ajax:

                return JsonResponse({
                    "success": False,
                    "message": message
                }, status=401)

            messages.error(
                request,
                message
            )

            return redirect("login")

        # =========================
        # LOGIN USER
        # =========================

        login(
            request,
            user
        )

        # =========================
        # REMEMBER ME
        # =========================

        if remember:

            request.session.set_expiry(
                60 * 60 * 24 * 30
            )  # 30 DAYS

        else:

            request.session.set_expiry(0)

        # =========================
        # SUCCESS RESPONSE
        # =========================

        success_message = "Login successful."

        redirect_url = reverse("home")

        if is_ajax:

            return JsonResponse({
                "success": True,
                "message": success_message,
                "redirect_url": redirect_url,
                "user": {
                    "id": user.id,
                    "email": user.email,
                }
            })

        messages.success(
            request,
            success_message
        )

        return redirect(redirect_url)

from django.contrib import messages
from django.contrib.auth import logout
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View


class LogoutView(View):

    # =========================
    # POST LOGOUT
    # =========================

    def post(self, request):

        is_ajax = request.headers.get(
            "X-Requested-With"
        ) == "XMLHttpRequest"

        # =========================
        # LOGOUT SAFELY
        # =========================

        if request.user.is_authenticated:

            logout(request)

            # CLEAR SESSION COMPLETELY
            request.session.flush()

        # =========================
        # SUCCESS RESPONSE
        # =========================

        success_message = (
            "Logged out successfully."
        )

        redirect_url = reverse("product_list")

        # =========================
        # AJAX RESPONSE
        # =========================

        if is_ajax:

            return JsonResponse({
                "success": True,
                "message": success_message,
                "redirect_url": redirect_url
            })

        # =========================
        # NORMAL RESPONSE
        # =========================

        messages.success(
            request,
            success_message
        )

        return redirect(redirect_url)

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import UserProfile


@login_required
def profile_view(request):

    profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    return render(
        request,
        "accounts/profile.html",
        {
            "user": request.user,
            "profile": profile
        }
    )

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import UserProfile


@login_required
def edit_profile_view(request):

    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == "POST":

        user.full_name = request.POST.get("full_name", "").strip()
        user.email = request.POST.get("email", "").strip()

        phone = request.POST.get("phone", "").strip()

        # Save in User table
        user.phone = phone
        user.save()

        # Save in Profile table
        profile.phone = phone
        profile.save()

        messages.success(request, "Profile updated successfully")
        return redirect("home")

    return render(request, "accounts/edit_profile.html", {
        "profile": profile,
    })

