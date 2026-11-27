# matthewfamily/forms.py
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class MemberRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        min_length=3,
        max_length=50,
        required=True,
        error_messages={'min_length': 'First name must be at least 3 letters long.'}
    )
    last_name = forms.CharField(
        min_length=3,
        max_length=50,
        required=True,
        error_messages={'min_length': 'Last name must be at least 3 letters long.'}
    )
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    
    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name', '').strip()
        if len(first_name) < 3:
            raise forms.ValidationError("First name must contain at least 3 letters.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name', '').strip()
        if len(last_name) < 3:
            raise forms.ValidationError("Last name must contain at least 3 letters.")
        return last_name

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name'].strip()
        user.last_name = self.cleaned_data['last_name'].strip()
        user.email = self.cleaned_data['email']
        user.is_active = False  # Enforce admin approval before first login
        if commit:
            user.save()
        return user