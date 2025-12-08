from django.urls import path
from .views import LoginView, ForgotPasswordView, ResetPasswordView, LogoutView, ProfileView


urlpatterns = [
    path('login', LoginView.as_view({'post': 'login'}), name='login'),
    path('logout/<int:user_id>', LogoutView.as_view({'post': 'logout'}), name='logout'),
    path('forgot-password', ForgotPasswordView.as_view({'post': 'forgot_password'}), name='forgot_password'),
    path('reset-password', ResetPasswordView.as_view({'post': 'reset_password'}), name='reset_password'),
    path('profile/<int:id>', ProfileView.as_view({'get': 'retrieve', 'patch': 'update'}), name='get_and_update_profile'),

]