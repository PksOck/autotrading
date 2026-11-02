"""Network diagnostics must never retain credentials embedded in request URLs."""

import logging
import re


class RedactURLs(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        message = re.sub(
            r"(?i)([?&](?:t|q|token|api_key|apikey|key)=)[^&\s\"']+", r"\1[redacted]", message
        )
        message = re.sub(r"/bot[^/\s]+/", "/bot[redacted]/", message)
        record.msg, record.args = message, ()
        return True


def configure_network_logging() -> None:
    for name in (
        "httpx",
        "httpcore.connection",
        "httpcore.http11",
        "httpcore.http2",
        "httpcore.proxy",
        "httpcore.socks_proxy",
    ):
        logger = logging.getLogger(name)
        if not any(isinstance(item, RedactURLs) for item in logger.filters):
            logger.addFilter(RedactURLs())
        logger.setLevel(logging.WARNING)
