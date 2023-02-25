from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

# Create your views here.
def loginview(request):
    if request.method == "GET":
        nextloc = request.GET.get("next")
        return render(request, "account/login.html", {
            "next": nextloc
        })
    else:
        # get username +pswd
        username = request.POST.get("username")
        userpswd = request.POST.get("password")
        # try to authenticate
        user = authenticate(username = username, password = userpswd)
        if user is not None:
            login(request, user)
            return redirect("signup-index")
        else:
            return redirect("login")


def logoutview(request):
    logout(request)
    return redirect("login")


def signupview(request):
    if request.method == "GET":
        return render(request, "account/signup.html", {
            "uniqueerror": False
        })
    elif request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm = request.POST.get("confirm")
        if not first_name or not last_name or not username or not email or not password or not confirm:
            return redirect("signup")
        if not (password == confirm):
            return redirect("signup")
        if User.objects.filter(username=username):
            return render(request, "account/signup.html", {
                "first_name": first_name,
                "last_name": last_name,
                "username": username,
                "email": email,
                "password": password,
                "confirm": confirm,
                "uniqueerror": True
            })
        User.objects.create_user(username, email, password, first_name=first_name, last_name=last_name)
        return redirect("login")