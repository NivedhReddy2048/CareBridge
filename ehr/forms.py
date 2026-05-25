from django import forms
from .models import EHRRecord, DocumentAttachment

class EHRRecordForm(forms.ModelForm):
    class Meta:
        model = EHRRecord
        fields = ['title', 'record_type', 'date_of_record', 'notes']
        widgets = {
            'date_of_record': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'record_type': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class DocumentAttachmentForm(forms.ModelForm):
    class Meta:
        model = DocumentAttachment
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,image/*'}),
        }
