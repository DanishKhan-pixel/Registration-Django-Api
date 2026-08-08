GENDER_CHOICES = (
    ('male', 'Male'),
    ('female', 'Female'),
    ('other', 'other'),
)

TYPE_CHOICES = (
    ('hard_logout', 'Hard Logout'),
    ('token_expire', 'Token Expire'),
)

LOGIN_TYPE_CHOICES = (
    ('email', 'Email'),
    ('phone', 'Phone'),
    ('google', 'Google'),
    ('facebook', 'Facebook'),
    ('apple', 'Apple'),
)
TOKEN_TYPE_CHOICES = (
    ('email_verification', 'Email Verification'),
    ('subscription_token', 'Subscription Token'),
    ('forgot_password', 'Password Forgotten'),
)


MEDIA_TYPES_CHOICES = (
    ('image', 'Image'),
    ('video', 'Video'),
    ('document', 'Document'),
)