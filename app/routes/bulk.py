from fastapi import APIRouter, HTTPException
from app.models import BulkParseRequest, BulkParseResponse, BulkParseItemResult, ErrorResponse, MAX_BULK_NOTICES
from app.parser import parse_notice, ParseError

router = APIRouter()

@router.post(
    "/parse/bulk",
    response_model=BulkParseResponse,
    responses={422: {"model": ErrorResponse}, 400: {"model": ErrorResponse}}
)
def parse_bulk(req: BulkParseRequest):
    if len(req.notices) > MAX_BULK_NOTICES:
        raise HTTPException(
            status_code=400,
            detail={"error": "too_many_notices", "detail": f"Maximum {MAX_BULK_NOTICES} notices allowed per bulk request"}
        )

    results = []
    success_count = 0

    for notice_text in req.notices:
        try:
            parsed = parse_notice(notice_text)
            results.append(BulkParseItemResult(input=notice_text, result=parsed, error=None))
            success_count += 1
        except ParseError as e:
            results.append(BulkParseItemResult(input=notice_text, result=None, error=str(e)))

    # Settlement rule: charge only if at least one notice parses successfully.
    # If all fail (success_count == 0), return HTTP 422 to trigger x402 settlement cancellation.
    if success_count == 0:
        raise HTTPException(
            status_code=422,
            detail={"error": "unparseable", "detail": "All notices in bulk payload failed to parse; no payment charged."}
        )

    return BulkParseResponse(results=results)
