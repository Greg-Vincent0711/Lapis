import logging
import requests
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def retrieveAccessToken(authCode: str):
    oauth_URL = "https://discord.com/api/oauth2/token"
    data = {
        'grant_type': 'authorization_code',
        'code': authCode,
        'redirect_uri': os.getenv("REDIRECT_URI")
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    try:
        response = requests.post(
            oauth_URL,
            data=data,
            headers=headers,
            auth=(os.getenv("CLIENT_ID"), os.getenv("CLIENT_SECRET"))
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Discord token retrieval failed: {e}", exc_info=True)
        raise  # rethrow so the Lambda invocation fails visibly


def getUserInfo(accessToken: str):
    userDataURL = "https://discord.com/api/users/@me"
    headers = {
        "Authorization": f"Bearer {accessToken}"
    }
    try:
        response = requests.get(userDataURL, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Discord user info retrieval failed: {e}", exc_info=True)
        raise
