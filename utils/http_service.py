import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class HttpService:
    @staticmethod
    def get(url, params=None):
        response = requests.get(url, params=params)
        return response.json() if response.ok else response.text

    @staticmethod
    def post(url, data=None):
        response = requests.post(url, json=data)
        return response.json() if response.ok else response.text

    @staticmethod
    def patch(url, data=None):
        response = requests.patch(url, json=data)
        return response.json() if response.ok else response.text

    @staticmethod
    def delete(url, data=None):
        response = requests.delete(url, json=data)
        return response.json() if response.ok else response.text

def update_ezviz_config(ezv_key, ezv_secret):
    """
    Update EZVIZ configuration in ML service
    """
    try:
        url = f"{settings.ML_BASE_URL}dashboard/config/ezviz/update"
        payload = {
            "ezv_key": ezv_key,
            "ezv_secret": ezv_secret
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise exception for bad status codes
        
        return True, response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error updating EZVIZ config: {str(e)}")
        return False, str(e)
    except Exception as e:
        logger.error(f"Unexpected error in update_ezviz_config: {str(e)}")
        return False, str(e)