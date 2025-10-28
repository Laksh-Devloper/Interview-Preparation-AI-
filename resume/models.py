from django.db import models

class Resume(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    file = models.FileField(upload_to='resumes/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name if self.name else f"Resume {self.id}"
