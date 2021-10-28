import datetime
import iso8601

__all__ = ("parse_timestamp",)


def parse_timestamp(timestamp: str) -> datetime.datetime:
    """

    Parameters
    ----------
    timestamp: :class:`str`
        The timestamp to be parsed, in an iso8601 format.

    Returns
    -------
    :class:`datetime.datetime`
        The parsed timestamp.

    """
    return iso8601.parse_date(timestamp, datetime.timezone.utc)
