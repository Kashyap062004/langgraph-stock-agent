from langchain_core.tools import tool
import yfinance as yf


@tool
def get_stock_price(ticker: str):
    """Get the latest stock price for a given ticker symbol."""

    stock = yf.Ticker(ticker)
    data = stock.history(period="1d")

    if data.empty:
        return f"Could not retrieve data for {ticker}"

    price = data["Close"].iloc[-1]

    return f"The latest price of {ticker} is {price:.2f}"


@tool
def get_stock_history(ticker: str, period: str = "1mo"):
    """Get historical stock price data for a given ticker and period."""

    stock = yf.Ticker(ticker)
    data = stock.history(period=period)

    if data.empty:
        return f"Could not retrieve historical data for {ticker}"

    return data.tail(10).to_string()


@tool
def get_stock_fundamentals(ticker: str) -> str:
    """Get fundamental information about a stock including market cap, P/E ratio, revenue, profit, and 52-week range."""

    try:
        stock = yf.Ticker(ticker)

        info = stock.info

        if not info:
            return f"No fundamental data found for '{ticker}'."

        fields = {
            "Company": info.get("longName"),
            "Sector": info.get("sector"),
            "Industry": info.get("industry"),
            "Market Cap": info.get("marketCap"),
            "Current Price": info.get("currentPrice"),
            "P/E Ratio": info.get("trailingPE"),
            "Forward P/E": info.get("forwardPE"),
            "EPS": info.get("trailingEps"),
            "52 Week High": info.get("fiftyTwoWeekHigh"),
            "52 Week Low": info.get("fiftyTwoWeekLow"),
            "Dividend Yield": info.get("dividendYield"),
            "Currency": info.get("currency"),
        }

        lines = [
            f"{key}: {value}"
            for key, value in fields.items()
            if value is not None
        ]

        if not lines:
            return f"No fundamental data found for '{ticker}'."

        return f"Fundamentals for {ticker}:\n" + "\n".join(lines)

    except Exception as e:
        return f"Error fetching fundamentals for '{ticker}': {str(e)}"

@tool
def get_stock_news(ticker: str) -> str:
    """Get the latest news articles for a given stock ticker."""

    try:
        stock = yf.Ticker(ticker)
        news_items = stock.news[:5]

        if not news_items:
            return f"No recent news found for '{ticker}'."

        lines = []

        for item in news_items:
            content = item.get("content", item)

            title = content.get("title", "Untitled")

            publisher = (
                content.get("provider") or {}
            ).get("displayName", "Unknown source")

            lines.append(f"- {title} ({publisher})")

        return f"Recent news for {ticker}:\n" + "\n".join(lines)

    except Exception as e:
        return f"Error fetching news for '{ticker}': {str(e)}"


@tool
def compare_stocks(ticker_a: str, ticker_b: str) -> str:
    """Compare two stocks using their current price and 52-week high and low."""

    try:
        lines = []

        for ticker in (ticker_a, ticker_b):
            stock = yf.Ticker(ticker)
            fast = stock.fast_info

            # IMPORTANT: fast_info's dict-style keys are camelCase
            # ("lastPrice", "yearHigh", "yearLow") — fast.get("last_price")
            # silently returns None instead of raising, since .get() simply
            # doesn't find a key by that name. The snake_case names ARE
            # valid on this object, but only as ATTRIBUTES (fast.last_price),
            # not as .get() dict keys. Using getattr with a None default
            # keeps this safe even if a future yfinance version renames or
            # drops one of these fields.
            price = getattr(fast, "last_price", None)
            high = getattr(fast, "year_high", None)
            low = getattr(fast, "year_low", None)

            if price is None:
                continue

            lines.append(
                f"{ticker}: "
                f"Price=${price:.2f}, "
                f"52W High={high}, "
                f"52W Low={low}"
            )

        if not lines:
            return "Unable to compare the requested stocks."

        return "Comparison:\n" + "\n".join(lines)

    except Exception as e:
        return f"Error comparing stocks: {e}"

TOOLS = [
    get_stock_price,
    get_stock_history,
    get_stock_fundamentals,
    get_stock_news,
    compare_stocks,
]