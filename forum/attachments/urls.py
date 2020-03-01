
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin

from forum.attachments.views import upload

urlpatterns = [
    url(r'^$', upload, name='upload_img'),  
] 
