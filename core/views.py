from django.shortcuts import render

def login_view(request):
    # is_authenticated - False 
    return render(request, 'core/login.html', {'user': {'is_authenticated': False}})

def signup_view(request):
    return render(request, 'core/signup.html', {'user': {'is_authenticated': False}})

def profile_view(request):
    return render(request, 'core/profile.html', {'user': {'is_authenticated': True}})