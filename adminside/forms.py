from django import forms
from .models import Feedback
from .models import Store

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['email', 'feedback']

class StoreForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = ['store_name', 'location', 'description', 'logo']
