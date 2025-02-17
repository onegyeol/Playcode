from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import SignUpForm

def login_view(request):  # 로그인
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")  # 홈으로 리다이렉트 (홈 URL은 `urls.py`에 설정되어야 합니다)
        else:
            messages.error(request, "Wrong email or password!")

    return render(request, "accounts/login.html")

def logout_view(request): # 로그아웃
    logout(request)
    return redirect("home")

def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])  # 비밀번호 암호화
            user.save()
            return redirect('login')  # 회원가입 후 로그인 페이지로 리다이렉트
        else:
            messages.error(request, 'Please correct the error below.')

    else:
        form = SignUpForm()

    return render(request, 'accounts/signup.html', {'form': form})
