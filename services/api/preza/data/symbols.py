"""Exchange-specific ticker spelling for each provider (UCITS ETFs trade in London and Xetra)."""

YAHOO_SUFFIX = {
    "LSE": ".L",
    "LSEETF": ".L",
    "IBIS": ".DE",
    "IBIS2": ".DE",
    "XETRA": ".DE",
    "AEB": ".AS",
}
STOOQ_SUFFIX = {"LSE": ".uk", "LSEETF": ".uk", "IBIS": ".de", "IBIS2": ".de", "XETRA": ".de"}
US_EXCHANGES = {None, "", "SMART", "NASDAQ", "NYSE", "ARCA", "AMEX", "BATS", "ISLAND", "NMS"}


def yahoo_symbol(symbol: str, exchange: str | None) -> str:
    base = symbol.replace(".", "-") if exchange in US_EXCHANGES else symbol
    return base + YAHOO_SUFFIX.get((exchange or "").upper(), "")


def stooq_symbol(symbol: str, exchange: str | None) -> str:
    if exchange in US_EXCHANGES:
        return f"{symbol.lower().replace('.', '-')}.us"
    return symbol.lower() + STOOQ_SUFFIX.get((exchange or "").upper(), "")
