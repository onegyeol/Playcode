from django.shortcuts import render

def home(request):
    if request.user.is_authenticated:
        # 로그인 상태일 경우 main_login.html을 보여줌
        return render(request, "main/main_login.html")
    else:
        # 로그인하지 않은 경우 main_not_login.html을 보여줌
        return render(request, "main/main_not_login.html")
