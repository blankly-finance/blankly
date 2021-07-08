from datetime import datetime as dt


def is_datetime_naive(datetime_obj: dt):
    if datetime_obj.tzinfo is None or datetime_obj.tzinfo.utcoffset(datetime_obj) is None:
        return True
    return False
