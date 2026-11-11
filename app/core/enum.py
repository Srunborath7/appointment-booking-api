from enum import Enum
from enum import IntEnum

class StatusCode(IntEnum):
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    TOO_MANY_REQUESTS = 429
    INTERNAL_SERVER_ERROR = 500

class RoleName(str, Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    NURSE = "nurse"
    CASHIER = "cashier"
    PATIENT = "patient"

class AdminStatus(str, Enum):
    active = "active"
    inactive = "inactive"

class ClientSurface(str, Enum):
    PORTAL = "portal"
    MOBILE = "mobile"
