from django.db import models

# Create your models here.



class SlackToken(models.Model):
    username = models.CharField(max_length=100, unique=True)
    token = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Slack Token for {self.username}"

    class Meta:
        verbose_name = "Slack Token"
        verbose_name_plural = "Slack Tokens"



