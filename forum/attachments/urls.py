
from django.conf.urls import url
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
from django.conf.urls import include

from forum.attachments.views import upload


urlpatterns = [
    url(r'^$', upload, name='upload_img'),  
] 
