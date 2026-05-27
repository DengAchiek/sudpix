from django import forms

from apps.media_management.models import MediaAsset
from apps.projects.models import ProjectBrief, ProjectFeedback, RevisionRequest


INPUT_CLASS = (
    "mt-2 w-full rounded-2xl border border-white/10 bg-primary px-4 py-3 "
    "text-sm text-white outline-none transition focus:border-gold/50"
)


class ProjectBriefForm(forms.ModelForm):
    class Meta:
        model = ProjectBrief
        fields = ("objective", "audience", "deliverables", "creative_direction", "reference_links")
        widgets = {
            "objective": forms.Textarea(attrs={"rows": 3, "placeholder": "What should this project achieve?"}),
            "audience": forms.TextInput(attrs={"placeholder": "Primary audience or guests"}),
            "deliverables": forms.Textarea(attrs={"rows": 3, "placeholder": "Photos, reels, logo pack, brand deck..."}),
            "creative_direction": forms.Textarea(attrs={"rows": 3, "placeholder": "Look, mood, colours, or must-have moments"}),
            "reference_links": forms.Textarea(attrs={"rows": 2, "placeholder": "Reference links or notes"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT_CLASS


class ProjectFeedbackForm(forms.ModelForm):
    class Meta:
        model = ProjectFeedback
        fields = ("area", "message")
        widgets = {
            "area": forms.Select(),
            "message": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Share feedback with the SudPix team..."}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT_CLASS


class RevisionRequestForm(forms.ModelForm):
    class Meta:
        model = RevisionRequest
        fields = ("media_asset", "title", "details")
        widgets = {
            "media_asset": forms.Select(),
            "title": forms.TextInput(attrs={"placeholder": "e.g. Update opening title card"}),
            "details": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Describe the exact adjustment and desired result."}
            ),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["media_asset"].queryset = (
            MediaAsset.objects.filter(project=project).order_by("title")
            if project
            else MediaAsset.objects.none()
        )
        self.fields["media_asset"].required = False
        self.fields["media_asset"].empty_label = "General project revision"
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT_CLASS


class ProjectApprovalForm(forms.Form):
    note = forms.CharField(
        required=False,
        label="Approval note",
        widget=forms.Textarea(
            attrs={
                "rows": 2,
                "class": INPUT_CLASS,
                "placeholder": "Optional final note for the SudPix team.",
            }
        ),
    )
