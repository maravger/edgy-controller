from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^app_stats/', views.controller.get_app_stats),
    url(r'^vertical_scaling/', views.controller.scale_vertically)
]
