from django import forms
from .models import CustomUser

class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, min_length=6)
    confirm_password = forms.CharField(widget=forms.PasswordInput, min_length=6)

    class Meta:
        model = CustomUser
        fields = ['email', 'username', 'password']  # confirm_password는 포함되지 않음

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")  # 입력한 패스워드
        confirm_password = cleaned_data.get("confirm_password")  # 재입력한 패스워드

        if password != confirm_password:  # 비밀번호가 일치하지 않을 때
            raise forms.ValidationError("Passwords do not match")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])  # 비밀번호를 암호화
        if commit:
            user.save()
        return user
