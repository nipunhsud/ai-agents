from django.contrib import admin
from .models import Conversation, Message, Document, GmailToken

admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(Document)
admin.site.register(GmailToken) 