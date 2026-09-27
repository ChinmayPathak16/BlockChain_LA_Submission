from typing import Optional, List
from pydantic import BaseModel, Field

class DelayNotice(BaseModel):
    train_number: str          # 4-5 digits
    station_code: str          # 2-5 uppercase letters
    expected_time: str         # "HH:MM" 24h
    reason: Optional[str] = None  # original-language text if present, else null

MAX_NOTICE_LENGTH = 2_000   # characters; enforced server-side
MAX_BULK_NOTICES  = 20

class SingleParseRequest(BaseModel):
    notice: str = Field(..., max_length=MAX_NOTICE_LENGTH)

class BulkParseRequest(BaseModel):
    notices: List[str] = Field(..., max_length=MAX_BULK_NOTICES)

class BulkParseItemResult(BaseModel):
    input: str
    result: Optional[DelayNotice] = None
    error: Optional[str] = None

class BulkParseResponse(BaseModel):
    results: List[BulkParseItemResult]

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
