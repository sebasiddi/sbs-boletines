from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('boletin/', views.boletin_view, name='boletin'),
    path('boletin/<str:trimestre>/', views.boletin_view, name='boletin_trimestre'),

]
