from django.conf.urls import url

from forum.search.views import search

urlpatterns = [    
    url(r'^/?(?P<page>[\d]*)?/?$', search, name='search'),   
]
