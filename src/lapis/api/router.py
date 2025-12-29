'''
Presentation Layer(http requests, responses)
'''
from typing import Callable, Dict, Tuple
from src.lapis.api.models.http_models import APIRequest, APIResponse

class Router:
    def __init__(self):
        # Dictionary mapping (HTTP method, path pattern) tuples to handler functions
        # Example: {("GET", "/users"): get_users_handler, ("POST", "/users"): create_user_handler}
        self.routes: Dict[Tuple[str, str], Callable] = {}
    
    '''
        Keep track of routes
        Store a handler function for a specific method and path
        Example: register("GET", "/users/{id}", get_user_by_id)
    '''
    def register(self, method: str, path_pattern: str, handler_fn: Callable):
        self.routes[(method, path_pattern)] = handler_fn
    
    '''
    Find and execute the appropriate handler
    '''
    def route(self, request: APIRequest) -> APIResponse:
        requestInfo = (request.method, request.path)
        
        # if we have an exact route registered for this method and path
        if requestInfo in self.routes:
            handler_fn = self.routes[requestInfo]
            # call the handler matching the APIRequest type
            return handler_fn(request)
        
        # otherwise, iterate over all possible routes we have
        # path_pattern is stored within the router
        for (method, path_pattern), handler in self.routes.items():
            # Check if HTTP method matches AND path pattern matches
            # ex: method="GET" and path_pattern="/users/{id}" matches request path "/users/123"
            if method == request.method and self.pathPatternsMatch(path_pattern, request.path):
                return handler(request)
        
        return APIResponse(404, {"error": "Route not found"}).to_lambda_response()
    
    '''
        Pattern matching for paths like /locations/{name}
        specificPath is a APIRequest defined portion. 
        The user may send something like POST /helpme/{id} for ex which is not valid
    '''
    def pathPatternsMatch(self, routePattern: str, specificPath: str) -> bool:
        route_segments = routePattern.split("/")
        specific_path_segments = specificPath.split("/")
        
        # number of segments between general route like /users and a specific route like "/users/123/posts" must match
        # Example: "/users" has 2 parts, "/users/123/posts" has 4 parts
        if len(route_segments) != len(specific_path_segments):
            return False
        
        # Compare each segment of the pattern with the corresponding path segment
        for route_segment, specific_path_segment in zip(route_segments, specific_path_segments):
            # If pattern segment is a wildcard (like {id} or {name}), it matches anything
            if route_segment.startswith("{") and route_segment.endswith("}"):
                continue  # Wildcard matches anything
            
            # If it's not a wildcard, the segments must match exactly
            # Example: "users" must equal "users"
            if route_segment != specific_path_segment:
                return False
        return True

router = Router()
print("All routes",router.routes)