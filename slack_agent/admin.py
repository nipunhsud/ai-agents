from django.contrib import admin
from .models import SlackToken

# Register your models here.

@admin.register(SlackToken)
class SlackTokenAdmin(admin.ModelAdmin):
    list_display = ('username','token', 'created_at', 'updated_at')
    search_fields = ('username',)
    readonly_fields = ('created_at', 'updated_at')