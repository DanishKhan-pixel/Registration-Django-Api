import requests
from typing import List, Dict, Optional
from django.conf import settings


SUBSCRIPTION_BASE_URL = settings.SUBSCRIPTION_BASE_URL
def get_active_subscriptions(org_ids: List[int]) -> Dict[int, Dict]:
    """
    Fetch active subscriptions for given organization IDs from the subscription service.
    
    Args:
        org_ids (List[int]): List of organization IDs
        
    Returns:
        Dict[int, Dict]: Dictionary mapping organization ID to subscription details
                        Returns empty dict if API call fails
    """
    try:
        # Convert list of IDs to comma-separated string
        org_ids_str = ','.join(map(str, org_ids))
        
        # Make API request
        response = requests.get(
            f"{SUBSCRIPTION_BASE_URL}/subscriptions/external/active-subscriptions",
            params={'org_ids': org_ids_str},
            timeout=5  # 5 seconds timeout
        )
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            if data.get('status') and data.get('results'):
                # Convert list to dictionary for easier lookup
                return {
                    sub['organization_id']: {
                        'plan_name': sub['plan_name'],
                        'expiry_date': sub['expiry_date'],
                        'payment_method': sub['payment_method'],
                    }
                    for sub in data['results']
                }
        
        # Return empty dict if API call fails or response is invalid
        return {}
        
    except Exception as e:
        # Log the error if needed
        print(f"Error fetching subscriptions: {str(e)}")
        return {} 