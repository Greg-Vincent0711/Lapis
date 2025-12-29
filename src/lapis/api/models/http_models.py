from typing import Any, Dict, Optional
import json
from attr import dataclass

# dataclass decorator auto generates double underscore(dunder) boilerplate methods
# __init__, __repr__, __eq__, for ex
@dataclass
class APIRequest:
    method: str
    path: str
    query_params: Optional[Dict[str, str]] = None
    body: Dict[str, Any] = None
    path_params: Dict[str, str] = None
    cognito_user_id: Optional[str] = None
    author_id: Optional[str] = None
    
    
    # decorator means: we don't need to call self to use this method
    # cls refers to the class itself as a parameter. this is a factory method which is why we use classmethod here
    # entry point function of this api. See db_handler.py for more info
    @classmethod
    def from_lambda_event(cls, event: dict) -> 'APIRequest':
        """Parse Lambda event"""
        method = event.get("requestContext", {}).get("http", {}).get("method", "")
        path = event.get("rawPath", "")
        
        # Parse query string parameters
        query_params = {}
        query_string = event.get("queryStringParameters")
        if query_string:
            query_params = query_string
        elif event.get("rawQueryString"):
            # Parse raw query string if queryStringParameters is not available
            for param in event.get("rawQueryString", "").split("&"):
                if "=" in param:
                    key, value = param.split("=", 1)
                    query_params[key] = value
        
        body = {}
        if event.get("body"):
            try:
                body = json.loads(event["body"])
            except json.JSONDecodeError:
                body = {}
        
        # Extract path parameters generically
        path_params = {}
        path_segments = path.strip("/").split("/")
        # This will be enhanced by router pattern matching, but extract common patterns
        if len(path_segments) >= 2 and path_segments[0] == "locations":
            path_params['location_name'] = path_segments[1]
        
        cognito_user_id = (
            event.get("requestContext", {})
            .get("authorizer", {})
            .get("jwt", {})
            .get("claims", {})
            .get("sub")
        )    
        return cls(
            method=method,
            path=path,
            body=body,
            query_params=query_params,
            path_params=path_params,
            cognito_user_id=cognito_user_id,
        )

class APIResponse:
    def __init__(self, status_code: int, body: Dict[str, Any] | str):
        self.status_code = status_code
        self.body = body if isinstance(body, dict) else {"message": body}
    
    def to_lambda_response(self) -> dict:
        """Convert to Lambda response format"""
        return {
            "statusCode": self.status_code,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true",
                "Content-Type": "application/json"
            },
            "body": json.dumps(self.body)
        }