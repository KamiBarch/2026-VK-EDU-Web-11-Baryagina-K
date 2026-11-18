


from django.contrib.auth import login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect

def login_view(request):
    form = AuthenticationForm(
        request,
        data=request.POST or None,
    )

    if request.method == "POST" and form.is_valid():
        auth_login(request, form.get_user())
        return redirect("index")

    return render(request, "core/login.html", {"form": form})
def signup_view(request):
    return render(request, 'core/signup.html', {'user': {'is_authenticated': False}})

def profile_view(request):
    return render(request, 'core/profile.html', {'user': {'is_authenticated': True}})