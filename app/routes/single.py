from fastapi import APIRouter, HTTPException
from app.models import SingleParseRequest, DelayNotice, ErrorResponse
from app.parser import parse_notice, ParseError

router = APIRouter()

@router.post(
    "/parse",
    response_model=DelayNotice,
    responses={422: {"model": ErrorResponse}}
)
def parse_single(req: SingleParseRequest):
    try:
        return parse_notice(req.notice)
    except ParseError as e:
        raise HTTPException(
            status_code=422,
            detail={"error": "unparseable", "detail": str(e)}
        )
