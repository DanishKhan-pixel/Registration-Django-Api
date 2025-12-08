from django.urls import path
from authentication.views import LoginHistoryView

urlpatterns = [
    path('', LoginHistoryView.as_view({'get': 'list'}), name='login_history'),
    path('/user/<int:user_id>', LoginHistoryView.as_view({'get': 'retrieve'}), name='login_history_user'),
]
