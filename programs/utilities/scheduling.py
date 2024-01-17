from croniter import croniter
from datetime import datetime

def get_next_date_from_cron(cron_str: str) -> datetime:
    """
    Returns the next date an action will occur based on
    the provided cron string.
    """
    cron = croniter(
        cron_str, # The cron string
        datetime.now(), # start date
        day_or=False, # or_day
        hash_id="unique" # hash id
    )
    return cron.get_next(datetime)
