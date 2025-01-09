from django.db import models

from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.contrib.auth.models import User
import uuid
import time


class APICredentials(models.Model):
    """
    Model to store API credentials and unique identifiers.
    
    Attributes:
        unique_value (str): 8-character unique identifier
        username (str): Username associated with the credentials
        secret_key (str): Secret key for API authentication
        github_api (str): GitHub API token
        created_at (datetime): Timestamp when the record was created
        updated_at (datetime): Timestamp when the record was last updated
    """
    
    unique_value = models.CharField(
        max_length=8,
        unique=True,
        validators=[
            MinLengthValidator(8),
            MaxLengthValidator(8)
        ],
        help_text="8-character unique identifier"
    )
    
    username = models.CharField(
        max_length=150,
        help_text="Username for API access"
    )
    
    secret_key = models.CharField(
        max_length=255,
        help_text="GitHub API token"
    )
    
    github_api = models.CharField(
        max_length=255,
        unique=True,
        help_text="GitHub API token"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "API Credential"
        verbose_name_plural = "API Credentials"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.username} - {self.unique_value}"
    
    def save(self, *args, **kwargs):
        # Ensure unique_value is exactly 8 characters
        if len(self.unique_value) != 8:
            raise ValueError("unique_value must be exactly 8 characters")
        super().save(*args, **kwargs)