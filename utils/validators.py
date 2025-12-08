from django.core.exceptions import ValidationError
import re

DISPOSABLE_EMAIL_DOMAINS = {"tempmail.com", "10minutemail.com", "mailinator.com"}
PASSWORD_PATTERN = re.compile(
    r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@#$%^&+=!]).{8,}$"
)


def validate_password(password):
    """Validate a password and raise a ValidationError if invalid."""
    if not PASSWORD_PATTERN.fullmatch(password):
        raise ValidationError(
            "Password must be at least 8 characters long, include one uppercase letter, "
            "one lowercase letter, one number, and one special character (@#$%^&+=!).",
            code="invalid_password"
        )
    return password

def validate_email(email):
    """Validate an email address and raise a ValidationError if invalid."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(pattern, email):
        raise ValidationError("Invalid email format. Please enter a valid email address.")

    domain = email.split("@")[-1]
    if domain in DISPOSABLE_EMAIL_DOMAINS:  # Assuming you have a list of disposable email domains
        raise ValidationError("Disposable email addresses are not allowed. Please use a valid email.")
    return email


def validate_username(username):
    """Validate a username and raise a ValidationError if invalid."""
    pattern = r"^[a-zA-Z][a-zA-Z0-9._]{2,19}$"

    if not re.match(pattern, username):
        raise ValidationError(
            "Username must start with a letter, be 3-20 characters long, and contain only letters, numbers, dots, and underscores."
        )

    if ".." in username or "__" in username or "._" in username or "_. " in username:
        raise ValidationError("Username cannot contain consecutive dots or underscores.")

    return username


def validate_numeric_only(value):
    """Validate that a field contains only numbers (no alphabets)."""
    if value and not re.match(r'^[0-9]+$', str(value)):
        raise ValidationError("This field must contain only numbers (no alphabets allowed).")
    return value


def validate_file_size(value):
    filesize = value.size

    if filesize > 1048576:
        raise ValidationError("You cannot upload file more than 1Mb")
    return value

def validate_positive_value(value):
    if value is not None and value <= 0:
        raise ValidationError("ID Value must be positive")
    return value

