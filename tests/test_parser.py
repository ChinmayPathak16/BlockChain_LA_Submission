import pytest
from app.parser import parse_notice, ParseError
from app.models import DelayNotice

def test_good_01_english():
    text = "Train 12951 arriving at NDLS expected time 14:30 due to signal failure"
    notice = parse_notice(text)
    assert notice.train_number == "12951"
    assert notice.station_code == "NDLS"
    assert notice.expected_time == "14:30"
    assert notice.reason == "signal failure"

def test_good_02_hindi():
    text = "ट्रेन 12137 CSMT आगमन 09:15 कारण तकनीकी खराबी"
    notice = parse_notice(text)
    assert notice.train_number == "12137"
    assert notice.station_code == "CSMT"
    assert notice.expected_time == "09:15"
    assert notice.reason == "तकनीकी खराबी"

def test_good_03_marathi():
    text = "गाडी 11019 PUNE वेळ 18.45 मुळे हवामान खराब"
    notice = parse_notice(text)
    assert notice.train_number == "11019"
    assert notice.station_code == "PUNE"
    assert notice.expected_time == "18:45"
    assert notice.reason == "हवामान खराब"

def test_good_04_dot_time():
    text = "Special Train 12345 to HWH arriving at 08.30"
    notice = parse_notice(text)
    assert notice.train_number == "12345"
    assert notice.station_code == "HWH"
    assert notice.expected_time == "08:30"
    assert notice.reason is None

def test_good_05_noise_words():
    text = "[NOTICE] PNR check 12002 BCT platform 3 expected at 22:10 due to track maintenance"
    notice = parse_notice(text)
    assert notice.train_number == "12002"
    assert notice.station_code == "BCT"
    assert notice.expected_time == "22:10"
    assert notice.reason == "track maintenance"

def test_bad_01_missing_train_number():
    text = "Train arriving at NDLS expected time 14:30 due to fog"
    with pytest.raises(ParseError) as exc_info:
        parse_notice(text)
    assert "missing train_number" in str(exc_info.value)

def test_bad_02_missing_time():
    text = "Train 12951 arriving at NDLS due to engine fault"
    with pytest.raises(ParseError) as exc_info:
        parse_notice(text)
    assert "missing expected_time" in str(exc_info.value)

def test_bad_03_missing_station_code():
    text = "Train 12951 arriving at expected time 14:30"
    with pytest.raises(ParseError) as exc_info:
        parse_notice(text)
    assert "missing station_code" in str(exc_info.value)

def test_bad_04_empty_input():
    with pytest.raises(ParseError) as exc_info:
        parse_notice("")
    assert "missing train_number" in str(exc_info.value)

def test_bad_05_phone_number_no_train():
    text = "Call 9876543210 for info at station NDLS 25:99"
    with pytest.raises(ParseError) as exc_info:
        parse_notice(text)
    assert ("missing train_number" in str(exc_info.value) or "missing expected_time" in str(exc_info.value))
