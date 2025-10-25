# Discord OAuth Setup
import requests
import os
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
    response = requests.post(oauth_URL, data=data, headers=headers, auth=(os.getenv("CLIENT_ID"), os.getenv("CLIENT_SECRET")))
    response.raise_for_status()
    return response.json()

# Send this response back to the frontend
def getUserInfo(accessToken: str):
    userDataURL = "https://discord.com/api/users/@me"
    headers = {
        "Authorization": f"Bearer {accessToken}"
    }
    response = requests.get(userDataURL, headers=headers)
    response.raise_for_status()
    return response.json()