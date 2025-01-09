from django.contrib import admin
from .models import APICredentials

# Register your models here.
@admin.register(APICredentials)
class APICredentialsAdmin(admin.ModelAdmin):
    list_display = ('username', 'unique_value', 'secret_key', 'github_api', 'created_at', 'updated_at')
    search_fields = ('username', 'unique_value')
    readonly_fields = ('created_at', 'updated_at')
