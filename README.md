# airbnb-mcp-server
An MCP server for scraping Airbnb listings without requiring an API key, using web scraping techniques.

## Key Characteristics
- **No API Key Required**: Utilizes web scraping (via BeautifulSoup, requests, and selenium) since the Airbnb API is not public.
- **Tools**: 
  - `search_airbnb_listings`: Scrapes listings by location, dates, and filters, returning detailed JSON data.
  - `scrape_airbnb_listing_info`: Extracts comprehensive details from a single listing URL, returning a structured text summary.

## Installation
Install using uv and pip from this GitHub repository:
```bash
uv pip install --from git+https://github.com/yourusername/airbnb-mcp-server