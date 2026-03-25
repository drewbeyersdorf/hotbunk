from hotbunk.throttle_detector import is_throttle_signal, parse_throttle_message

def test_detects_rate_limit_message():
    assert is_throttle_signal("Rate limit exceeded. Please wait") is True
    assert is_throttle_signal("Rate limited. Waiting") is True
    assert is_throttle_signal("You've hit your usage limit") is True

def test_ignores_normal_output():
    assert is_throttle_signal("Hello world") is False
    assert is_throttle_signal("") is False
    assert is_throttle_signal("Running task...") is False

def test_parse_wait_time():
    msg = parse_throttle_message("Rate limit exceeded. Please wait 5 minutes")
    assert msg.wait_seconds > 0

def test_parse_no_wait_time():
    msg = parse_throttle_message("Rate limit exceeded")
    assert msg.wait_seconds == 300  # default 5 min
