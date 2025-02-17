from django.urls import path
from . import views  # views.py에서 작성한 로그인 후 이동할 뷰를 불러옵니다.
from accounts.views import logout_view

urlpatterns = [
    path('', views.home, name='home'),  # /main 경로 설정
    path('logout/', logout_view, name='logout'),
]
