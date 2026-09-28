from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm

User = get_user_model()


class AdminUserCreateForm(UserCreationForm):
    """Used by staff on the in-app admin dashboard to create accounts."""

    email = forms.EmailField(required=False)
    is_staff = forms.BooleanField(
        required=False, label="Grant staff/admin access"
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2", "is_staff")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email", "")
        user.is_staff = self.cleaned_data.get("is_staff", False)
        if commit:
            user.save()
        return user


class AdminUserEditForm(forms.ModelForm):
    """Used by staff to edit an existing account's basic details."""

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "is_staff", "is_active")


class AdminSetPasswordForm(SetPasswordForm):
    """Lets staff set a new password for another user's account."""
    pass


class PredictionForm(forms.Form):
    gender = forms.ChoiceField(choices=[('female','Female'),('male','Male')])
    race_ethnicity = forms.ChoiceField(choices=[('group A','Group A'),('group B','Group B'),('group C','Group C'),('group D','Group D'),('group E','Group E')])
    parental_education = forms.ChoiceField(choices=[
        ('some high school','Some high school'),('high school','High school'),('some college','Some college'),
        ("associate's degree", "Associate's degree"),("bachelor's degree", "Bachelor's degree"),("master's degree", "Master's degree")])
    lunch = forms.ChoiceField(choices=[('free/reduced','Free/Reduced'),('standard','Standard')])
    test_preparation = forms.ChoiceField(choices=[('none','None'),('completed','Completed')])
    reading_score = forms.FloatField(min_value=0, max_value=100, widget=forms.NumberInput(attrs={'step':'0.1'}))
    writing_score = forms.FloatField(min_value=0, max_value=100, widget=forms.NumberInput(attrs={'step':'0.1'}))
