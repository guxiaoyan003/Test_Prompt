from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = 'basic'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='basic:server_list', permanent=False), name='home'),
    path('server/list/', views.server_list, name='server_list'),
    path('server/add/', views.server_add, name='server_add'),
    path('server/update/', views.server_update, name='server_update'),
    path('server/delete/', views.server_delete, name='server_delete'),
    path('model/list/', views.model_list, name='model_list'),
    path('model/add/', views.model_add, name='model_add'),
    path('model/update/', views.model_update, name='model_update'),
    path('model/delete/', views.model_delete, name='model_delete'),
    path('prompt/dis/', views.prompt_dis, name='prompt_dis'),
    path('prompt/run/', views.prompt_run, name='prompt_run'),
]
