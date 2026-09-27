from fastapi import APIRouter, HTTPException
from app.models import SingleParseRequest, DelayNotice, ErrorResponse
from app.parser import parse_notice, ParseError

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok"}

@router.post(
    "/parse/preview",
    response_model=DelayNotice,
    responses={422: {"model": ErrorResponse}}
)
def parse_preview(req: SingleParseRequest):
    try:
        notice = parse_notice(req.notice)
        # Truncate fields to demo shape without giving full value, omit reason
        truncated_train = notice.train_number[:2] + "*" * (len(notice.train_number) - 2)
        truncated_station = notice.station_code[:1] + "*" * (len(notice.station_code) - 1)
        truncated_time = notice.expected_time[:3] + "**"
        
        return DelayNotice(
            train_number=truncated_train,
            station_code=truncated_station,
            expected_time=truncated_time,
            reason=None
        )
    except ParseError as e:
        raise HTTPException(
            status_code=422,
            detail={"error": "unparseable", "detail": str(e)}
        )
