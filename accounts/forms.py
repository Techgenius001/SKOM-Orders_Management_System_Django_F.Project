from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserChangeForm, UserCreationForm

from .models import User


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'workplace', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        for field in self.fields.values():
            field.widget.attrs.update(
                {
                    'class': 'mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none',
                }
            )
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'workplace', 'role')


class SignupForm(CustomUserCreationForm):
    class Meta(CustomUserCreationForm.Meta):
        fields = ('username', 'email', 'phone', 'workplace', 'password1', 'password2')


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update(
                {
                    'class': 'mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none',
                }
            )

