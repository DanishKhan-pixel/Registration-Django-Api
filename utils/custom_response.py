from rest_framework import status
from rest_framework.response import Response
import re


def True_Response_200(message, data, **kwargs):
    """
    This function will return the true(ok) response with a 200 status code.
    It accepts additional keyword arguments to be included in the response.
    """
    response = {
        "status": True,
        # "status_code": 200,
        "message": message,
        "results": data
    }

    response.update(kwargs)

    return Response(response, status=status.HTTP_200_OK)


def Created_Response_201(message, data, **kwargs):
    """
    This function will return the object created response with 201 status code
    """
    response = {
        "status": True,
        # "status_code": 200,
        "message": message,
        "results": data
    }

    response.update(kwargs)

    return Response(response, status=status.HTTP_200_OK)



def Exception_Response_400(message, errors=None):
    """
    This function will return the exception response with 400 status code
    """
    response = {"status": False, "message": message, "results": []}
    if errors is not None:
        response["errors"] = errors
    return Response(response, status=status.HTTP_400_BAD_REQUEST)

def Exception_Response_402(message):
    """
    This function will return the exception response with 400 status code
    """
    return Response({"status": False, "message": message,
                    "results": []}, status=status.HTTP_402_PAYMENT_REQUIRED)


def Except_Exception_Response_400(e, errors=None):
    """
    This function returns a 400 error response with human-readable messages.
    It ensures that field names are included when validation errors occur.
    """
    try:
        if errors is not None:
            # If errors are passed directly, use them
            error_details = errors
        else:
            error_details = e.args[0]

        if isinstance(error_details, dict):
            messages = []

            # Handle non-field errors
            if 'non_field_errors' in error_details:
                messages.append(error_details['non_field_errors'][0])

            # Iterate through all field errors
            for field, error_list in error_details.items():
                if field != "non_field_errors":
                    # Ensure error_list is iterable
                    if isinstance(error_list, list):
                        error_message = error_list[0]  # Get the first error message
                    else:
                        error_message = str(error_list)  # Convert non-list errors to string

                    messages.append(f"{field.replace('_', ' ').capitalize()}: {error_message}")

            message = " | ".join(messages)  # Concatenate multiple errors in a readable format

        else:
            message = str(error_details)  # Handle unexpected error formats

    except Exception as ex:
        message = "An unexpected error occurred: " + str(ex)
        error_details = None

    response = {
        "status": False,
        "message": message,
        "results": []
    }
    if error_details is not None:
        response["errors"] = error_details
    return Response(response, status=status.HTTP_400_BAD_REQUEST)

# class IsActiveAndIsNotDelete(permissions.BasePermission):
#
#     def has_permission(self, request, view):
#         if request.user.is_active is True and request.user.is_delete is False and request.user.status=='Default':
#             return True
#         return False