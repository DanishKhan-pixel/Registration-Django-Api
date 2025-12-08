import random
import string
from authentication.models import Token
from django.db.models import Q, Value
from django.core.mail import EmailMessage
from django.conf import settings
from utils.custom_response import Except_Exception_Response_400
from django.db.models.functions import Concat


EXCLUDED_FIELDS = ["created_at", "updated_at", "is_deleted", "deleted_at"]


def generate_unique_token(alpha_count=4, digit_count=2):
    """
    Generate a unique token with a dynamic number of alphabets and digits.

    :param alpha_count: Number of alphabetic characters (default: 4)
    :param digit_count: Number of numeric characters (default: 2)
    :return: A shuffled alphanumeric string that is unique in the Token model.
    """
    while True:
        letters = ''.join(random.choices(string.ascii_uppercase, k=alpha_count))  # Uppercase alphabets
        digits = ''.join(random.choices(string.digits, k=digit_count))  # Digits
        token = list(letters + digits)
        random.shuffle(token)  # Shuffle to mix letters and digits
        otp = ''.join(token)

        if not Token.objects.filter(code=otp).exists():  # Ensure uniqueness
            return otp

def dynamic_filter(model, search_fields=None, search_query=None, sort_by=None, is_trash=False, **kwargs):
    """
    Dynamically filters a model based on provided kwargs and applies a search query if given.

    :param model: Django model class to filter.
    :param search_fields: List of fields to apply the search filter on.
    :param search_query: Search keyword to look for in specified fields.
    :param kwargs: Additional filtering criteria as keyword arguments.
    :return: Filtered queryset.
    """
    kwargs.pop('page_size', None)
    kwargs.pop('search', None)
    kwargs.pop('page', None)
    kwargs.pop('sort', None)
    if is_trash:
        kwargs['is_deleted'] = True
    else:
        kwargs["is_deleted"] = False

    queryset = model.objects.filter(**kwargs)

    # Support annotated full name search when requested
    if search_fields and "full_name" in search_fields:
        queryset = queryset.annotate(full_name_search=Concat("first_name", Value(" "), "last_name"))

    if search_query and search_fields:
        search_filters = Q()
        for field in search_fields:
            if field == "full_name":
                search_filters |= Q(**{"full_name_search__icontains": search_query})
            else:
                search_filters |= Q(**{f"{field}__icontains": search_query})
        queryset = queryset.filter(search_filters)

    if sort_by:
        queryset = queryset.order_by(sort_by)
    else:
        queryset = queryset.order_by("-updated_at")

    return queryset

def send_email(subject, body, emails):
    try:
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.EMAIL_HOST_USER,
            to=emails,
        )
        email.send()
        return True
    except Exception as e:
        return Except_Exception_Response_400(e)


