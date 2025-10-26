"""
Ticker Utilities for RAG Service
Extracts stock ticker symbols from user queries
"""
import re
from typing import Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Common stock ticker patterns
TICKER_KEYWORDS = {
    'apple': 'AAPL',
    'tesla': 'TSLA',
    'microsoft': 'MSFT',
    'amazon': 'AMZN',
    'google': 'GOOGL',
    'alphabet': 'GOOGL',
    'meta': 'META',
    'facebook': 'META',
    'nvidia': 'NVDA',
    'amd': 'AMD',
    'intel': 'INTC',
    'netflix': 'NFLX',
    'twitter': 'X',
    'spacex': 'TSLA',  # Often associated
    'berkshire': 'BRK.B',
    'walmart': 'WMT',
    'jpmorgan': 'JPM',
    'visa': 'V',
    'mastercard': 'MA',
    'coca-cola': 'KO',
    'pepsi': 'PEP',
    'boeing': 'BA',
    'disney': 'DIS',
    'nike': 'NKE',
}


def extract_ticker_from_question(question: str) -> Optional[str]:
    """
    Extract stock ticker symbol from a user question
    
    Args:
        question: User's question text
        
    Returns:
        Stock ticker symbol or None if not found
        
    Examples:
        "What is AAPL's revenue?" -> "AAPL"
        "Tell me about Tesla" -> "TSLA"
        "MSFT stock price" -> "MSFT"
        "How is the market doing?" -> None
    """
    if not question:
        return None
    
    question_lower = question.lower()
    
    # Method 1: Look for explicit ticker symbols (1-5 uppercase letters)
    # Pattern: word boundary + 1-5 uppercase letters + word boundary
    ticker_pattern = re.findall(r'\b[A-Z]{1,5}\b', question)
    
    # Filter out common English words that might match pattern
    english_words = {'I', 'A', 'USA', 'US', 'UK', 'CEO', 'CFO', 'IPO', 'ETF', 'NYSE', 'NASDAQ', 'SEC'}
    ticker_candidates = [t for t in ticker_pattern if t not in english_words]
    
    if ticker_candidates:
        logger.info(f"Found ticker candidate: {ticker_candidates[0]}")
        return ticker_candidates[0]
    
    # Method 2: Check for company names in the question
    for company_name, ticker in TICKER_KEYWORDS.items():
        # Use word boundaries to avoid partial matches
        if re.search(r'\b' + re.escape(company_name) + r'\b', question_lower):
            logger.info(f"Matched company name '{company_name}' -> {ticker}")
            return ticker
    
    # Method 3: Check for possessive forms (e.g., "Apple's revenue")
    for company_name, ticker in TICKER_KEYWORDS.items():
        if re.search(r'\b' + re.escape(company_name) + r"'s?\b", question_lower):
            logger.info(f"Matched possessive form '{company_name}' -> {ticker}")
            return ticker
    
    logger.info("No ticker found in question")
    return None


def extract_all_tickers(question: str) -> List[str]:
    """
    Extract all possible ticker symbols from a question
    
    Args:
        question: User's question text
        
    Returns:
        List of ticker symbols found
    """
    tickers = []
    question_lower = question.lower()
    
    # Find explicit tickers
    ticker_pattern = re.findall(r'\b[A-Z]{1,5}\b', question)
    english_words = {'I', 'A', 'USA', 'US', 'UK', 'CEO', 'CFO', 'IPO', 'ETF', 'NYSE', 'NASDAQ', 'SEC'}
    tickers.extend([t for t in ticker_pattern if t not in english_words])
    
    # Find company names
    for company_name, ticker in TICKER_KEYWORDS.items():
        if re.search(r'\b' + re.escape(company_name) + r'\b', question_lower):
            if ticker not in tickers:
                tickers.append(ticker)
    
    return tickers


def is_ticker_in_question(question: str, ticker: str) -> bool:
    """
    Check if a specific ticker is mentioned in the question
    
    Args:
        question: User's question
        ticker: Ticker symbol to check
        
    Returns:
        True if ticker is mentioned
    """
    if not question or not ticker:
        return False
    
    question_upper = question.upper()
    ticker_upper = ticker.upper()
    
    # Direct ticker match
    if re.search(r'\b' + re.escape(ticker_upper) + r'\b', question_upper):
        return True
    
    # Check if company name associated with ticker is in question
    question_lower = question.lower()
    for company_name, t in TICKER_KEYWORDS.items():
        if t.upper() == ticker_upper:
            if company_name in question_lower:
                return True
    
    return False


def normalize_ticker(ticker: str) -> str:
    """
    Normalize ticker to standard format
    
    Args:
        ticker: Raw ticker symbol
        
    Returns:
        Normalized ticker (uppercase, trimmed)
    """
    if not ticker:
        return ""
    
    return ticker.strip().upper()


def get_company_name_for_ticker(ticker: str) -> Optional[str]:
    """
    Get company name for a ticker symbol
    
    Args:
        ticker: Ticker symbol
        
    Returns:
        Company name or None
    """
    ticker_upper = ticker.upper()
    
    # Reverse lookup in TICKER_KEYWORDS
    for company_name, t in TICKER_KEYWORDS.items():
        if t == ticker_upper:
            return company_name.title()
    
    return None


def add_ticker_to_keywords(company_name: str, ticker: str) -> None:
    """
    Add a new company name -> ticker mapping
    
    Args:
        company_name: Company name (lowercase)
        ticker: Ticker symbol (will be normalized)
    """
    TICKER_KEYWORDS[company_name.lower()] = normalize_ticker(ticker)
    logger.info(f"Added mapping: {company_name} -> {ticker}")


if __name__ == "__main__":
    # Example usage
    print("=== RAG Ticker Utils Examples ===\n")
    
    # Test ticker extraction
    test_questions = [
        "What is AAPL's revenue growth?",
        "Tell me about Tesla's production",
        "How is Microsoft performing?",
        "NVDA stock analysis",
        "What's the market outlook?",
        "Compare AAPL and MSFT",
    ]
    
    print("Ticker Extraction Tests:")
    for q in test_questions:
        ticker = extract_ticker_from_question(q)
        print(f"  Q: {q}")
        print(f"  → Ticker: {ticker}\n")
    
    # Test multiple ticker extraction
    print("\nExtract All Tickers:")
    multi_ticker_q = "Compare AAPL, MSFT, and Tesla performance"
    all_tickers = extract_all_tickers(multi_ticker_q)
    print(f"  Q: {multi_ticker_q}")
    print(f"  → Tickers: {all_tickers}\n")
    
    # Test ticker presence check
    print("Ticker Presence Check:")
    q = "What is Apple's revenue?"
    print(f"  Q: {q}")
    print(f"  → Contains 'AAPL': {is_ticker_in_question(q, 'AAPL')}")
    print(f"  → Contains 'TSLA': {is_ticker_in_question(q, 'TSLA')}\n")
    
    # Test company name lookup
    print("Company Name Lookup:")
    for ticker in ['AAPL', 'TSLA', 'MSFT', 'UNKNOWN']:
        company = get_company_name_for_ticker(ticker)
        print(f"  {ticker} -> {company}")
    
    print("\n=== Examples Complete ===")

