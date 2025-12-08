import os



PULSSE_SUBSCRIPTION_URL = os.environ.get("PULSSE_SUBSCRIPTION_URL")


urls = {
    "PULSSE_SUBSCRIPTION_URL" : PULSSE_SUBSCRIPTION_URL,

}

endpoints = {
    "SUBSCRIPTIONS": '/subscriptions',
    "PLANS": '/subscriptions/plans',

}
