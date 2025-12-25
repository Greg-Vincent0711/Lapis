'''
similar to db_services, just for OAuth. Connects to Discord OAuth API
implement the business service portion for these 2 functions

'''

import logging
import requests
import os
from src.lapis.api.repositories.db import get_credentials, create_credentials, get_table
from src.lapis.api.repositories.oauth import *
from src.lapis.api.middleware.errors import *
from src.lapis.api.models.http_models import APIRequest, APIResponse
from src.lapis.api.middleware.errors import UnauthorizedError
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_credentials_attempt(request: APIRequest, authCode: str = None):
    table = get_table()
    if not request.cognito_user_id:
        raise UnauthorizedError("Cognito User ID is required")

    # both api calls: get_credentials and create_credentials throw errors. presentation layer catches
    items = get_credentials(table, request.cognito_user_id)
    
    if not items:
        if not authCode:
            raise UnauthorizedError("An authcode is required to retrieve the Discord author_id.")
        accessToken = retrieveAccessToken(authCode)
        author_id = getAuthorDataFromDiscord(accessToken["access_token"])["id"]
        create_credentials(table, author_id, request.cognito_user_id)
        return
    return     

# get the author_ID here
def getAuthorDataFromDiscord(accessToken: str):
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


def retrieveAccessToken(authCode: str):
    oauth_URL = "https://discord.com/api/v10/oauth2/token"
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