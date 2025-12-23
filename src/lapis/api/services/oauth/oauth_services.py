'''
similar to db_services, just for OAuth
implement the business service portion for these 2 functions
'''

from src.lapis.api.repositories.db import get_credentials, create_credentials, get_table
from src.lapis.api.repositories.oauth import *
from src.lapis.api.middleware.errors import *
from src.lapis.api.models.http_models import APIRequest, APIResponse


def get_credentials_attempt(request: APIRequest) -> str:
    table = get_table()
    if not request.cognito_user_id:
        raise UnauthorizedError("Cognito User ID is required")

    if not request.author_id:
        raise UnauthorizedError("Author ID is required")

    # both api calls: get_credentials and create_credentials throw errors
    response = get_credentials(table, request.cognito_user_id)
    items = response.get("Items", [])

    if not items:
        create_credentials(table,request.author_id,request.cognito_user_id)
        return request.author_id

    return items[0]["Author_ID"]    