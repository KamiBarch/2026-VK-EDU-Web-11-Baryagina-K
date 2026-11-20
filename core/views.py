from django.contrib.auth import login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from django.contrib import auth
from django.contrib.auth.decorators import login_required
from .forms import LoginForm, RegisterForm, ProfileForm
from django.utils.translation import override



@override("en")
def login_view(request):
    next_url = request.POST.get(
        "next",
        request.GET.get("next", ""),
    ).strip()

    if not url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = ""

        if request.method == "POST":
            form = LoginForm(request=request, data=request.POST)

            if form.is_valid():
                auth.login(request, form.get_user())
                return HttpResponseRedirect(
                    next_url or reverse("index")
                )
        else:
            form = LoginForm(request=request)


    return render(
        request,
        "core/login.html",
        {
            "form": form,
            "next": next_url,
        },
    )


def signup_view(request):
    with override("en"):
        if request.method == "POST":
            form = RegisterForm(request.POST, request.FILES,)

            if form.is_valid():
                user = form.save()
                auth.login(request, user)
                return redirect("index")
        else:
            form = RegisterForm()

        return render(
            request,
            "core/signup.html",
            {"form": form},
        )


@login_required
def profile_view(request):
    with override("en"):
        profile = request.user.profile
        current_avatar_url = (
            profile.avatar.url if profile.avatar else None
        )

        if request.method == "POST":
            form = ProfileForm(
                request.user,
                request.POST,
                request.FILES,
            )

            if form.is_valid():
                form.save()
                return redirect("profile")
        else:
            form = ProfileForm(request.user)

        return render(
            request,
            "core/profile.html",
            {
                "form": form,
                "current_avatar_url": current_avatar_url,
            },
        )
