from django import forms


class JoinForm(forms.Form):
    email = forms.CharField(label='email')
    password = forms.CharField(label='password')
    confirm_password = forms.CharField(label='confirm_password')
    name = forms.CharField(label='name')

class LoginForm(forms.Form):
    email = forms.CharField(label='email')
    password = forms.CharField(label='password')

    def clean(self):
        cleaned_data = super(LoginForm, self).clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
