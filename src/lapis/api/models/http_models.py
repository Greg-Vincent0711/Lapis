from typing import Any, Dict, Optional
import json

# dataclass decorator auto generates double underscore boilerplate methods
# __init__, __repr__, __eq__, for ex
# NotImplementedError@dataclass
class APIRequest:
    method: str
    path: str
    body: Dict[str, Any]
    path_params: Dict[str, str]
    query_params: Optional[Dict[str, str]]
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
        
        body = {}
        if event.get("body"):
            try:
                body = json.loads(event["body"])
            except json.JSONDecodeError:
                body = {}
        
        # improve this later
        path_params = {}
        if path.startswith("/locations/") and len(path.split("/")) >= 3:
            path_params['location_name'] = path.split("/")[2]
        
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
            path_params=path_params,
            cognito_user_id=cognito_user_id
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
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Credentials": "true",
                "Content-Type": "application/json"
            },
            "body": json.dumps(self.body)
        }