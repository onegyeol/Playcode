# config/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),  # 로그인 URL 연결
    path('', include('main.urls')),  # 홈 페이지 URL 연결
]
