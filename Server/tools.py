from langchain_core.tools import tool
import yfinance as yf
import requests


@tool
def get_stock_price(ticker: str) -> str:
    """
    Fetch the current (or most recent close) price for a stock ticker.

    Use this when the user asks about a stock's current price, how it's
    trading today, or wants a quick quote (e.g. "What's TSLA trading at?").

    Args:
        ticker: The stock ticker symbol, e.g. "AAPL", "TSLA", "MSFT".
                Must be uppercase exchange ticker, not a company name.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.fast_info

        # fast_info's dict-style .get() keys are camelCase ("lastPrice",
        # "previousClose") — info.get("last_price") silently returns None
        # instead of erroring. The snake_case names only work as
        # ATTRIBUTES: info.last_price, not info.get("last_price").
        price = getattr(info, "last_price", None)
        prev_close = getattr(info, "previous_close", None)

        if price is None:
            return f"Error: could not find price data for ticker '{ticker}'. It may be an invalid symbol."
        change = price - prev_close if prev_close else None
        pct = (change / prev_close * 100) if change is not None and prev_close else None
        change_str = f", change: {change:+.2f} ({pct:+.2f}%)" if change is not None else ""
        return f"{ticker}: ${price:.2f}{change_str}"
    except Exception as e:
        return f"Error fetching price for '{ticker}': {str(e)}"

@tool
def get_stock_fundamentals(ticker: str) -> str:
    """
    Fetch key fundamental metrics for a company: P/E ratio, market cap,
    52-week high/low, dividend yield, and sector.

    Use this when the user asks about valuation, whether a stock is
    "expensive", company size, or fundamentals in general.

    Args:
        ticker: The stock ticker symbol, e.g. "AAPL".
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
            return f"Error: could not find fundamental data for ticker '{ticker}'."

        fields = {
            "Market Cap": info.get("marketCap"),
            "P/E Ratio (trailing)": info.get("trailingPE"),
            "P/E Ratio (forward)": info.get("forwardPE"),
            "52-Week High": info.get("fiftyTwoWeekHigh"),
            "52-Week Low": info.get("fiftyTwoWeekLow"),
            "Dividend Yield": info.get("dividendYield"),
            "Sector": info.get("sector"),
            "Industry": info.get("industry"),
        }
        lines = [f"{k}: {v}" for k, v in fields.items() if v is not None]
        return f"Fundamentals for {ticker}:\n" + "\n".join(lines)
    except Exception as e:
        return f"Error fetching fundamentals for '{ticker}': {str(e)}"


@tool
def get_stock_news(ticker: str) -> str:
    """
    Fetch recent news headlines related to a stock ticker.

    Use this when the user asks "what's happening with X", wants recent news,
    or asks why a stock moved.

    Args:
        ticker: The stock ticker symbol, e.g. "AAPL".
    """
    try:
        stock = yf.Ticker(ticker)
        news_items = stock.news[:5]
        if not news_items:
            return f"No recent news found for '{ticker}'."
        lines = []
        for item in news_items:
            content = item.get("content", item)
            title = content.get("title", "Untitled")
            publisher = (content.get("provider") or {}).get("displayName", "Unknown source")
            lines.append(f"- {title} ({publisher})")
        return f"Recent news for {ticker}:\n" + "\n".join(lines)
    except Exception as e:
        return f"Error fetching news for '{ticker}': {str(e)}"


@tool
def compare_stocks(ticker_a: str, ticker_b: str) -> str:
    """
    Compare two stocks side by side on price, market cap, and P/E ratio.
    Use this when the user explicitly wants a comparison between two companies
    (e.g. "Compare AAPL and MSFT").

    Args:
        ticker_a: First ticker symbol.
        ticker_b: Second ticker symbol.
    """
    try:
        results = {}
        for t in (ticker_a, ticker_b):
            stock = yf.Ticker(t)
            info = stock.info
            fast = stock.fast_info
            results[t] = {
                "price": getattr(fast, "last_price", None),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
            }
        lines = [f"{t}: price=${v['price']:.2f}, market_cap={v['market_cap']}, P/E={v['pe_ratio']}"
                  for t, v in results.items() if v["price"] is not None]
        if not lines:
            return f"Error: could not fetch comparable data for '{ticker_a}' and '{ticker_b}'."
        return "Comparison:\n" + "\n".join(lines)
    except Exception as e:
        return f"Error comparing '{ticker_a}' and '{ticker_b}': {str(e)}"


@tool
def search_uploaded_documents(query: str, ticker: str = "") -> str:
    """
    Search the current user's uploaded documents (10-Ks, 10-Qs, earnings
    call transcripts, research notes, etc.) for content relevant to the
    query. Use this when the user asks about "my document", "my report",
    "the filing I uploaded", or asks a question that seems to reference
    material you don't have from live market data (e.g. specific risk
    factors, management commentary, or details only found in a filing).

    Args:
        query: What to search for, in natural language (e.g. "revenue
            growth drivers", "risk factors related to supply chain").
        ticker: Optional. If the user's question is about a specific
            company's documents, pass its ticker (e.g. "AAPL") to narrow
            the search to only documents tagged with that ticker. Leave
            empty to search across all of the user's uploaded documents.
    """
    # This function's real body is intentionally never called by the LLM
    # directly — nodes.py's tool_node special-cases this tool name and
    # calls rag.search_documents() itself with user_id injected from graph
    # state, bypassing this body entirely. It exists here only so the tool
    # is included in TOOLS (and therefore in llm.bind_tools(TOOLS)) with the
    # right name/docstring/schema for the model to see and decide to call.
    # This fallback only runs if something invokes the tool directly outside
    # the normal graph flow (e.g. a unit test) — it has no user context, so
    # it correctly returns nothing rather than searching across all users.
    return "search_uploaded_documents must be called through the agent graph, not directly."


@tool
def get_my_watchlist_prices() -> str:
    """
    Fetch current prices for every ticker on the user's saved watchlist.
    Use this when the user asks "how's my watchlist doing", "check my
    saved stocks", or similar — takes no arguments, since it always means
    THIS user's own watchlist.
    """
    # Same pattern as search_uploaded_documents above — see nodes.py.
    return "get_my_watchlist_prices must be called through the agent graph, not directly."


TOOLS = [
    get_stock_price,
    get_stock_fundamentals,
    get_stock_news,
    compare_stocks,
    search_uploaded_documents,
    get_my_watchlist_prices,
]