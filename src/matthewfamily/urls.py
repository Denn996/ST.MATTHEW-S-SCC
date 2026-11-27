from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('calendar/', views.calendar, name='calendar'),
    path('treasury/', views.treasury, name='treasury'),
    path('approvals/', views.pending_approvals, name='pending_approvals'),
    path('approvals/approve/<int:user_id>/', views.approve_member, name='approve_member'),
    path('approvals/reject/<int:user_id>/', views.reject_member, name='reject_member'),
]
