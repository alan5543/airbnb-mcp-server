# airbnb-mcp-server
An MCP server for scraping Airbnb listings without requiring an API key, leveraging web scraping techniques to provide detailed accommodation data.

## Key Characteristics
- **No API Key Required**: Utilizes web scraping (via BeautifulSoup, requests, and Selenium) since the Airbnb API is not publicly available, making it accessible without credentials.
- **Real-Time Scraping**: Fetches live data from Airbnb, including listings, prices, and amenities, with robust error handling.
- **Two Powerful Tools**:
  - `search_airbnb_listings`: Scrapes multiple listings by location, dates, and filters, returning structured JSON data.
  - `scrape_airbnb_listing_info`: Extracts comprehensive details from a single listing URL, providing a formatted text summary.
- **Optimized for Telegram**: Designed for concise, sanitized output suitable for chat-based interfaces.

## Why This is Helpful
While traditional platforms like Airbnb’s website require manual browsing, this MCP server acts as a virtual travel assistant in your AI client. It excels at:
- **Contextual Searches**: Find listings based on natural language prompts without navigating complex interfaces.
- **Flexible Date Ranges**: Search across multiple days to spot the best deals.
- **Detailed Insights**: Access detailed listing info (e.g., amenities, host details) without visiting each page.
Think of it as having a personal Airbnb scout in your chat, remembering your preferences and delivering results instantly!

## Features
- Search listings by location, check-in/check-out dates, and guest numbers.
- Filter by maximum price and page limit for tailored results.
- Extract detailed info (e.g., beds, bathrooms, amenities) from individual listings.
- Handle multi-page scraping with deduplication for unique results.
- Save debug HTML (`debug_airbnb_page.html`) for troubleshooting.

## Prerequisites
- Python 3.13+
- Install [uv](https://github.com/astral-sh/uv) for dependency management:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh