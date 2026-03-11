from django.urls import path
from . import views
from .views import class_log_view


urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('boletin/', views.boletin_view, name='boletin'),
    path("class-log/", class_log_view, name="class_log"),
    path('boletin/<str:trimestre>/', views.boletin_view, name='boletin_trimestre'),

]

