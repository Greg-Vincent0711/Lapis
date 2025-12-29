# Backend API Issues to Fix

This document lists all issues found in the backend API code that must be fixed for the system to work correctly.

## Critical Issues (Will Cause Runtime Errors)

### 1. delete_handlers.py:32 - Wrong Function Registered
**File:** `src/lapis/api/handler_methods/delete_handlers.py`  
**Line:** 32  
**Issue:** The route registers `delete_image_url_attempt` instead of `delete_image_url_handler`  
**Current Code:**
```python
router.register("DELETE", "/locations/{location_name}/img", delete_image_url_attempt)
```
**Fix:** Should register the handler function, not the service function:
```python
router.register("DELETE", "/locations/{location_name}/img", delete_image_url_handler)
```

### 2. get_handlers.py:19 - Missing Return Statement
**File:** `src/lapis/api/handler_methods/get_handlers.py`  
**Line:** 19  
**Issue:** `get_location_handler` calls `retrieve_location` but doesn't return the result  
**Current Code:**
```python
def get_location_handler(request: APIRequest) -> APIResponse:
    try:
        queryParams = request.query_params
        retrieve_location(request.author_id, queryParams["location_name"])
    except UnauthorizedError as e:
        return APIResponse(401, str(e))
    # ... other exceptions
```
**Fix:** Must return the result:
```python
def get_location_handler(request: APIRequest) -> APIResponse:
    try:
        queryParams = request.query_params
        result = retrieve_location(request.author_id, queryParams["location_name"])
        return APIResponse(200, result)
    except UnauthorizedError as e:
        return APIResponse(401, str(e))
    # ... other exceptions
```

### 3. upsert_handlers.py:70 - Dict Accessed as Object Attribute
**File:** `src/lapis/api/handler_methods/upsert_handlers.py`  
**Line:** 70  
**Issue:** `body` is a dict but accessed with dot notation  
**Current Code:**
```python
authCode = body.authCode
```
**Fix:** Should use dict access:
```python
authCode = body["authCode"]
```

### 4. delete_handlers.py:11 - Dict Accessed as Object Attribute
**File:** `src/lapis/api/handler_methods/delete_handlers.py`  
**Line:** 11  
**Issue:** `params` is a dict but accessed with dot notation  
**Current Code:**
```python
res = delete_location_attempt(request.author_id, params.location_name)
```
**Fix:** Should use dict access:
```python
res = delete_location_attempt(request.author_id, params["location_name"])
```

### 5. delete_handlers.py:24 - Dict Accessed as Object Attribute
**File:** `src/lapis/api/handler_methods/delete_handlers.py`  
**Line:** 24  
**Issue:** Same issue in `delete_image_url_handler`  
**Current Code:**
```python
res = await delete_image_url_attempt(request.author_id, params.location_name)
```
**Fix:** Should use dict access:
```python
res = await delete_image_url_attempt(request.author_id, params["location_name"])
```

### 6. encryption.py:27 - Type Mismatch in decrypt Function
**File:** `src/lapis/api/services/encryption/encryption.py`  
**Line:** 27  
**Issue:** Function signature says it takes `str` but `Fernet.decrypt()` requires bytes  
**Current Code:**
```python
def decrypt(encryptedData: str):
    fernetInstance = getFernet()
    return fernetInstance.decrypt(encryptedData)
```
**Fix:** Should accept bytes or convert string to bytes:
```python
def decrypt(encryptedData: str | bytes):
    fernetInstance = getFernet()
    if isinstance(encryptedData, str):
        encryptedData = encryptedData.encode()
    return fernetInstance.decrypt(encryptedData)
```

### 7. db_services.py:45 - Missing Logger Import
**File:** `src/lapis/api/services/db/db_services.py`  
**Line:** 45  
**Issue:** `logger` is used but not imported  
**Current Code:** Uses `logger.error(msg)` but no logger import  
**Fix:** Add import at top:
```python
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
```

### 8. router.py - No Async Support
**File:** `src/lapis/api/router.py`  
**Issue:** Router doesn't handle async handler functions. `delete_image_url_handler` is async but router calls it synchronously  
**Current Code:**
```python
def route(self, request: APIRequest) -> APIResponse:
    # ...
    return handler_fn(request)  # Won't work for async functions
```
**Fix:** Need to detect and await async functions:
```python
import asyncio
import inspect

def route(self, request: APIRequest) -> APIResponse:
    # ...
    handler_fn = self.routes[requestInfo]
    if inspect.iscoroutinefunction(handler_fn):
        return asyncio.run(handler_fn(request))
    return handler_fn(request)
```

### 9. db_lambda.py:27 - Missing authCode Parameter
**File:** `src/lapis/api/db_lambda.py`  
**Line:** 27  
**Issue:** `get_credentials_attempt` is called without `authCode` parameter, but the function may require it  
**Current Code:**
```python
request.author_id = get_credentials_attempt(request)
```
**Fix:** The function signature shows `authCode` is optional, but logic may require it. Need to handle case where authCode is needed but not provided, or ensure it's only called when credentials already exist.

### 10. router.py:41 - Wrong Return Type
**File:** `src/lapis/api/router.py`  
**Line:** 41  
**Issue:** Returns `dict` instead of `APIResponse`  
**Current Code:**
```python
return APIResponse(404, {"error": "Route not found"}).to_lambda_response()
```
**Fix:** Should return `APIResponse` object, not the lambda response dict:
```python
return APIResponse(404, {"error": "Route not found"})
```

## Logic/Data Issues

### 11. db_services.py:70 - Type Mismatch in decrypt Call
**File:** `src/lapis/api/services/db/db_services.py`  
**Line:** 70  
**Issue:** `decrypt()` receives string but may need bytes, and `.decode()` is called on result  
**Current Code:**
```python
return decrypt(res['Attributes']['Coordinates']).decode()
```
**Fix:** Ensure decrypt handles string input correctly (see issue #6), or convert:
```python
coords_encrypted = res['Attributes']['Coordinates']
if isinstance(coords_encrypted, str):
    coords_encrypted = coords_encrypted.encode()
return decrypt(coords_encrypted).decode()
```

### 12. db_services.py:87 - Type Mismatch in decrypt Call
**File:** `src/lapis/api/services/db/db_services.py`  
**Line:** 87  
**Issue:** Similar issue - `.encode()` called before decrypt, but decrypt may expect bytes  
**Current Code:**
```python
decrypted_coords = decrypt(item['Coordinates'].encode()).decode()
```
**Fix:** See issue #6 - decrypt should handle both string and bytes

### 13. db_services.py:91 - Type Mismatch in decrypt Call
**File:** `src/lapis/api/services/db/db_services.py`  
**Line:** 91  
**Issue:** Same pattern  
**Current Code:**
```python
result["Image_URL"] = decrypt(item["Image_URL"].encode()).decode()
```
**Fix:** See issue #6

### 14. db_services.py:112 - Type Mismatch in decrypt Call
**File:** `src/lapis/api/services/db/db_services.py`  
**Line:** 112  
**Issue:** Same pattern  
**Current Code:**
```python
return decrypt(res['Item']['World_Seed'].encode()).decode()
```
**Fix:** See issue #6

### 15. db_services.py:137 - Type Mismatch in decrypt Call
**File:** `src/lapis/api/services/db/db_services.py`  
**Line:** 137  
**Issue:** Same pattern, but no `.encode()` call  
**Current Code:**
```python
delete_url = decrypt(res['Attributes']['Image_URL']).decode()
```
**Fix:** Should be consistent with other calls - add `.encode()` if decrypt expects bytes, or fix decrypt to handle strings

### 16. s3_fns.py:21 - Parameter Type Mismatch
**File:** `src/lapis/api/repositories/s3_fns.py`  
**Line:** 21  
**Issue:** Function expects Discord message object with `attachments` attribute, but called from API handler with different data structure  
**Current Code:**
```python
async def storeImageInS3(message) -> str | None:
    # ...
    image = message.attachments[0]  # Expects Discord message object
```
**Fix:** Need to clarify expected input type. If called from API, should accept image URL or base64 data instead of Discord message object.

### 17. upsert_handlers.py:49 - Parameter Type Mismatch
**File:** `src/lapis/api/handler_methods/upsert_handlers.py`  
**Line:** 49  
**Issue:** `body['message']` is passed to `create_image`, but `storeImageInS3` expects Discord message object  
**Current Code:**
```python
res = create_image(request.author_id, body["location_name"], body['message'])
```
**Fix:** Need to align data structure - either change `storeImageInS3` to accept the API format, or transform the data before calling.

## Error Handling Issues

### 18. Multiple Files - Exception Attribute Access
**Files:** `get_handlers.py`, `upsert_handlers.py`, `delete_handlers.py`  
**Issue:** Code accesses `e.status_code` and `e.message` on exceptions, but `APIError` class has these attributes. However, some exception handlers convert exceptions to strings first.  
**Examples:**
- `get_handlers.py:11` - `APIResponse(e.status_code, e.message)` - This is correct for APIError
- `get_handlers.py:21` - `APIResponse(401, str(e))` - Inconsistent, should use `e.status_code, e.message`
- `delete_handlers.py:14` - `APIResponse(401, str(e))` - Inconsistent

**Fix:** Standardize error handling - always use `e.status_code` and `e.message` for `APIError` subclasses, or always use `str(e)` consistently.

### 19. error_handler_middleware - Return Type Inconsistency
**File:** `src/lapis/api/middleware/errors.py`  
**Line:** 46, 51  
**Issue:** Middleware returns `dict` (from `to_lambda_response()`) but handler expects `APIResponse` or dict  
**Current Code:**
```python
return APIResponse(e.status_code, {"error": e.message}).to_lambda_response()
```
**Fix:** This is actually correct for Lambda, but ensure consistency - handlers should return `APIResponse` objects, and middleware converts to Lambda format.

### 20. db_lambda.py:42 - Exception Handling Returns Wrong Type
**File:** `src/lapis/api/db_lambda.py`  
**Line:** 42  
**Issue:** Exception handler returns `APIResponse(...).to_lambda_response()` which is correct, but should be consistent with middleware pattern.

## Code Quality Issues

### 21. handler_methods/__init__.py - Typo in Comment
**File:** `src/lapis/api/handler_methods/__init__.py`  
**Line:** 1  
**Issue:** Comment has typo "route handlersß" (extra ß character)  
**Fix:** Remove the ß character

### 22. db.py:181 - Incorrect Import Usage
**File:** `src/lapis/api/repositories/db.py`  
**Line:** 181  
**Issue:** Uses `boto3.dynamodb.conditions.Key` instead of imported `Key`  
**Current Code:**
```python
KeyConditionExpression=boto3.dynamodb.conditions.Key("Author_ID").eq(str(author_id))
```
**Fix:** Should use the imported `Key`:
```python
KeyConditionExpression=Key("Author_ID").eq(str(author_id))
```

### 23. db_services.py:34 - Function Name Mismatch
**File:** `src/lapis/api/services/db/db_services.py`  
**Line:** 34  
**Issue:** Function is named `create_seed` but called as `set_seed` in handler  
**Current Code:**
```python
def create_seed(author_id: str, seed: str):
```
But in `upsert_handlers.py:34`, it's called as:
```python
res = set_seed(request.author_id, body["seed"])
```
**Fix:** Either rename function to `set_seed` or update handler to call `create_seed`. Check repository layer - `db.py` has `set_seed` function, so service should probably be `set_seed` too.

### 24. Missing Query Params Parsing
**File:** `src/lapis/api/models/http_models.py`  
**Issue:** `from_lambda_event` doesn't parse query parameters from Lambda event  
**Current Code:** `query_params` is set to `None` by default and never populated  
**Fix:** Parse query string parameters from `event.get("queryStringParameters", {})` or `event.get("rawQueryString", "")`

### 25. Path Params Not Extracted for All Routes
**File:** `src/lapis/api/models/http_models.py`  
**Line:** 35-37  
**Issue:** Path params only extracted for `/locations/` routes, but other routes with path params won't work  
**Current Code:**
```python
if path.startswith("/locations/") and len(path.split("/")) >= 3:
    path_params['location_name'] = path.split("/")[2]
```
**Fix:** Make path param extraction generic to handle any `{param_name}` pattern, or extract based on registered route patterns.

### 26. db_lambda.py:29-32 - Path Modification Logic Issue
**File:** `src/lapis/api/db_lambda.py`  
**Lines:** 29-32  
**Issue:** Path is extracted from event, then modified after `APIRequest` is created, but the modification happens on the request object, not the original path used for routing  
**Current Code:**
```python
path = event.get("rawPath", "")
# strip "/prod"
if path.startswith("/prod"):
    request.path = path[len("/prod"):]
```
**Fix:** Should modify path before creating `APIRequest`, or ensure router uses the modified path.

## Summary

**Total Issues:** 26
- **Critical (Runtime Errors):** 10
- **Logic/Data Issues:** 7
- **Error Handling Issues:** 3
- **Code Quality Issues:** 6

All issues should be fixed before the backend can work correctly in production.

