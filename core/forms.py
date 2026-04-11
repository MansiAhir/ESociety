from django.contrib.auth.forms import UserCreationForm
from .models import User
from django import forms 


class UserSignupForm(UserCreationForm):

    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Password"})
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Confirm Password"})
    )

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "gender", "mobile", "role"]

        widgets = {
            "email": forms.EmailInput(attrs={"placeholder": "Email"}),
            "first_name": forms.TextInput(attrs={"placeholder": "First Name"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Last Name"}),
            "mobile": forms.TextInput(attrs={"placeholder": "Mobile Number"}),
            "gender": forms.RadioSelect(),  # This renders gender as radio buttons
        }


class UserLoginForm(forms.Form):
    # email = forms.EmailField()
    # password = forms.CharField(widget=forms.PasswordInput)
    email    = forms.EmailField(widget=forms.EmailInput(attrs={"placeholder": "Email Address"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder": "Password"}))



# ── Forgot-password flow ───────────────────────────────────────────────────────
 
class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        label="Registered Email Address",
        widget=forms.EmailInput(attrs={"placeholder": "Enter your registered email"}),
    )
 
 
class OTPVerifyForm(forms.Form):
    otp = forms.CharField(
        label="One-Time Password",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(
            attrs={"placeholder": "Enter 6-digit OTP", "inputmode": "numeric", "autocomplete": "one-time-code"}
        ),
    )
 
 
class SetNewPasswordForm(forms.Form):
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={"placeholder": "New password"}),
        min_length=8,
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={"placeholder": "Confirm new password"}),
    )
 
    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("new_password1")
        p2 = cleaned.get("new_password2")
        if p1 and p2 and p1 != p2:
            self.add_error("new_password2", "Passwords do not match.")
        return cleaned