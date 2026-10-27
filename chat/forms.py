
from django import forms
from .models import Message


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["text"]

        widgets = {
            "text": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "maxlength": 2000,
                "placeholder": "Tulis pesan...",
            }),
        }

        error_messages = {
            "text": {
                "required": "Pesan tidak boleh kosong.",
            }
        }

    def clean_text(self):
        text = self.cleaned_data["text"].strip()

        if not text:
            raise forms.ValidationError(
                "Pesan tidak boleh kosong."
            )

        return text
