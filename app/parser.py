import re
from app.models import DelayNotice

class ParseError(Exception):
    pass

# Known noise words excluded when detecting station codes
NOISE_WORDS = {
    "PNR", "SMS", "INFO", "NOTICE", "DELAY", "REASON", "DUE", 
    "HTTP", "HTTPS", "GET", "POST", "STATUS", "REF", "TRAIN", 
    "TIME", "ETA", "ETD", "BY", "FOR", "AND", "WITH"
}

def parse_notice(text: str) -> DelayNotice:
    r"""
    Parses messy Indian Railways delay notices into structured DelayNotice object.
    
    Order of extraction:
    1. train_number: first standalone 4-5 digit run (\b\d{4,5}\b). Required.
    2. station_code: first standalone run of 2-5 uppercase Latin letters (\b[A-Z]{2,5}\b)
       excluding NOISE_WORDS. Required.
    3. expected_time: \b([01]\d|2[0-3])[:.][0-5]\d\b, normalized to 'HH:MM'. Required.
    4. reason: optional text trailing after markers ('due to', 'reason:', 'कारण', 'मुळे').
    """
    if not text or not text.strip():
        raise ParseError("missing train_number")
    
    if not re.search(r'\d', text):
        raise ParseError("missing train_number")

    # 1. train_number
    train_match = re.search(r'\b\d{4,5}\b', text)
    if not train_match:
        raise ParseError("missing train_number")
    train_number = train_match.group(0)

    # 2. station_code
    station_matches = re.findall(r'\b[A-Z]{2,5}\b', text)
    station_code = None
    for candidate in station_matches:
        if candidate not in NOISE_WORDS:
            station_code = candidate
            break
    if not station_code:
        raise ParseError("missing station_code")

    # 3. expected_time
    time_match = re.search(r'\b([01]\d|2[0-3])[:.][0-5]\d\b', text)
    if not time_match:
        raise ParseError("missing expected_time")
    expected_time = time_match.group(0).replace('.', ':')

    # 4. reason (optional)
    reason = None
    markers_pattern = r'(?i)(?:due\s+to|reason:|कारण|मुळे)'
    marker_match = re.search(markers_pattern, text)
    if marker_match:
        raw_reason = text[marker_match.end():].strip()
        raw_reason = re.sub(r'^[:\-\s]+', '', raw_reason)
        if raw_reason:
            reason = raw_reason

    # Explicit schema validation — ValidationError surfaces before any response is sent
    return DelayNotice.model_validate({
        "train_number": train_number,
        "station_code": station_code,
        "expected_time": expected_time,
        "reason": reason,
    })
