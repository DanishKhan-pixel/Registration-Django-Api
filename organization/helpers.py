import requests
from utils.micro_services import urls, endpoints
from utils.custom_response import Exception_Response_400
from authentication.models import User


def check_users_limit(org_id):
    """Checks if an organization has reached its camera creation limit."""

    subscription_url = f"{urls['PULSSE_SUBSCRIPTION_URL']}{endpoints['SUBSCRIPTIONS']}"
    params = {"organization_id": org_id, "status": 1}
    organization_subscription = requests.get(subscription_url, params=params)
    response_json = organization_subscription.json()

    if not response_json.get("results"):
        return Exception_Response_400("No active subscription found for the organization.")

    plan_id = response_json["results"][0].get("plan")
    if not plan_id:
        return Exception_Response_400("Subscription plan ID is missing.")

    plans_url = f"{urls['PULSSE_SUBSCRIPTION_URL']}{endpoints['PLANS']}"
    plan_response = requests.get(f"{plans_url}/{plan_id}")
    plan_json = plan_response.json()
    no_of_users = plan_json.get("results", {}).get("no_of_users", 0)

    org_users_count = User.objects.filter(profile__organization=org_id, status=1).count()
    org_users_count -= 1
    if org_users_count >= no_of_users:
        return Exception_Response_400(
            "The active user creation limit has been reached. Please upgrade your plan or contact support for further assistance."
        )

    return True
