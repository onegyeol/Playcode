from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email" # 로그인 시 이메일 필드 사용
    REQUIRED_FIELDS = ["username"] # 추가 정보 입력 필드

    groups = models.ManyToManyField(
        Group,
        related_name="customuser_groups",  # 충돌 방지
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="customuser_permissions",  # 충돌 방지
        blank=True
    )

    def __str__(self):
        return self.email
