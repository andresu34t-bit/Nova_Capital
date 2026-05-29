from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('markets/', views.markets, name='markets'),
    path('contact/', views.contact, name='contact'),
    path('legal/', views.legal, name='legal'),
    path('faq/', views.faq, name='faq'),
]
