"""openbts.codes
response codes returned by NodeManager
"""
from enum import IntEnum

class OpenBTSCode(IntEnum):
    """Generic OpenBTS response code"""
    pass

class SuccessCode(OpenBTSCode):
    """Codes that are associated with a successful Nodemanager request.
    """
    OK = 200
    NoContent = 204

class ErrorCode(OpenBTSCode):
    """Codes that are associated with a failed Nodemanager request.
    """
    NotFound = 404
    InvalidRequest = 406
    ConflictingValue = 409
    StoreFailed = 500
    UnknownAction = 501
    ServiceUnavailable = 503

