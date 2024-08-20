# forms.py
from django import forms

class DistanceForm(forms.Form):
    source = forms.CharField(label='Source', max_length=100)
    destination = forms.CharField(label='Destination', max_length=100)
    mode_of_transport = forms.ChoiceField(
        choices=[
            ('bus', 'Bus'),
            ('train', 'Train'),
            ('metro', 'Metro'),
            ('car', 'Car'),
            ('bike', 'Bike'),
            ('bicycle', 'Bicycle'),
            ('walk', 'Walk'),
            ('rickshaw','Rickshaw'),
            ('activa','Activa')
        ],
        label='Mode of Transport'
    )
    is_electric = forms.ChoiceField(
        choices=[
            ('yes', 'Yes'),
            ('no', 'No')
        ],
        label='Is the transport electric?'
    )
    time_taken = forms.CharField(label='Time Taken', max_length=100)
    date = forms.DateField(widget=forms.SelectDateWidget, label='Date')
