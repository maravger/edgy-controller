from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^collector/', views.collect, name ='collector')
]
