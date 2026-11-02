import logging

from preza.security_logging import configure_network_logging


def test_sensitive_network_urls_are_redacted_idempotently(caplog):
    configure_network_logging()
    logger = logging.getLogger("httpx")
    count = len(logger.filters)
    configure_network_logging()
    assert len(logger.filters) == count
    with caplog.at_level(logging.INFO, logger="httpx"):
        logger.info("GET https://example.test/path?token=SYNTHETIC_TOKEN&x=1")
        logger.info("POST https://api.telegram.org/botSYNTHETIC_TOKEN/sendMessage")
    assert "SYNTHETIC_TOKEN" not in caplog.text
