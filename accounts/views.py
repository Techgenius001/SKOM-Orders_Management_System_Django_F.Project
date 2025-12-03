from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.views import LoginView as DjangoLoginView

from .forms import LoginForm, SignupForm
from .models import User


class SignUpView(CreateView):
    """Public registration view for new customers."""

    form_class = SignupForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        form.instance.role = User.Roles.CUSTOMER
        response = super().form_valid(form)
        messages.success(self.request, 'Account created! You can now log in.')
        return response


class LoginView(DjangoLoginView):
    """Styled login view using Tailwind widgets."""

    form_class = LoginForm
    template_name = 'registration/login.html'
