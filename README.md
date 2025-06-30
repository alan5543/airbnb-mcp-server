# Airbnb Scraper MCP Server
[![smithery badge](https://smithery.ai/badge/@alan5543/airbnb-mcp-server)](https://smithery.ai/server/@alan5543/airbnb-mcp-server)

## Introduction
The Airbnb Scraper MCP Server enables Large Language Models (LLMs) to retrieve detailed Airbnb listing information without needing an API key. Using web scraping, it collects comprehensive data on properties, including availability, pricing, amenities, and more, directly from Airbnb's website. This server integrates seamlessly with MCP-compatible clients (e.g., Claude Desktop) to enhance Airbnb search and analysis capabilities.

## Tools
The server provides two powerful tools for scraping Airbnb data. Below are their details, including function names, parameters, and return values, formatted for clarity:

### `search_airbnb_listings`
- **Function**: `search_airbnb_listings(place: str, checkin_date: str, checkout_date: str, adults: int = 1, children: int = 0, infants: int = 0, pets: int = 0, price_max: int = 1000, max_pages: int = 3) -> str`
- **Description**: Searches Airbnb for listings in a specified location and date range, fetching detailed information from individual listing pages.
- **Parameters**:
  - `place: str`: The location to search (e.g., "Hong Kong"). Use the English name of the location.
  - `checkin_date: str`: Check-in date in YYYY-MM-DD format (e.g., "2025-08-01").
  - `checkout_date: str`: Check-out date in YYYY-MM-DD format (e.g., "2025-08-06").
  - `adults: int` (default: 1): Number of adult guests.
  - `children: int` (default: 0): Number of child guests.
  - `infants: int` (default: 0): Number of infant guests.
  - `pets: int` (default: 0): Number of pets.
  - `price_max: int` (default: 1000): Maximum price per night in local currency. Specify your budget.
  - `max_pages: int` (default: 3): Maximum number of search result pages to scrape.
- **Returns**: A JSON string containing a list of listings, each with:
  - `listing_id`: Unique listing identifier.
  - `url`: Direct link to the listing with query parameters.
  - `title`: Sanitized listing title (max 50 characters).
  - `price`: Price (e.g., "$39 CAD per night").
  - `price_qualifier`: Price context (e.g., "per night").
  - `average_rating`: Rating (e.g., "4.78") or "N/A".
  - `rating_count`: Number of reviews.
  - `host_name`: Host's first name.
  - `host_is_verified`: Whether the host is verified (True/False).
  - `host_is_superhost`: Whether the host is a superhost (True/False).
  - `host_years`: Years the host has been active.
  - `host_months`: Months the host has been active.
  - `latitude`: Listing latitude.
  - `longitude`: Listing longitude.
  - `beds`: Number of beds (e.g., "2 beds").
  - `guests`: Number of guests (e.g., "4 guests").
  - `bedrooms`: Number of bedrooms (e.g., "2 bedrooms").
  - `bathrooms`: Number of bathrooms (e.g., "1 bath").
  - `amenities`: List of amenities (e.g., ["Wi-Fi", "Kitchen"]).
  - `location`: Neighborhood or specific location.
  - `image_urls`: List of image URLs.
  - `badges`: List of badges (e.g., ["NEW"]).
  - `listing_type`: Type of listing (e.g., "Private Room").
  - If no listings are found, returns a plain-text error message (e.g., "No Airbnb listings found for the given criteria, or the scraper was blocked.").

### `scrape_airbnb_listing_info`
- **Function**: `scrape_airbnb_listing_info(url: str, max_retries: int = 3) -> str`
- **Description**: Scrapes detailed information from a single Airbnb listing URL, including description, location, host details, and more.
- **Parameters**:
  - `url: str`: The Airbnb listing URL, optionally including query parameters like `check_in`, `check_out`, `guests`, and `adults` (e.g., "https://www.airbnb.ca/rooms/15956982?check_in=2025-08-01&check_out=2025-08-06&guests=1&adults=1").
  - `max_retries: int` (default: 3): Number of attempts to fetch HTML content if the initial request fails.
- **Returns**: A structured text string with the following sections:
  - `Airbnb Description`: Listing title and description.
  - `Airbnb Location`: Location details and coordinates.
  - `Airbnb Host`: Host details (name, verification status, superhost status).
  - `Airbnb Rating and Reviews`: Rating and review information.
  - `Airbnb House Rules`: House rules and safety information.
  - `Airbnb Prices Info`: Pricing, capacity, and listing type.
  - `Airbnb Image Info`: Image details and badges.
  - If data cannot be retrieved, returns an error message (e.g., "Invalid Airbnb URL provided.").

## Manual Configuration
To set up the Airbnb Scraper MCP Server locally:
1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   ```
2. **Set Up UV**:
   Install UV (a Python package and project manager). Follow the official UV documentation for installation instructions.
3. **Install Dependencies**:
   Install required Python packages using UV:
   ```bash
   uv pip install requests beautifulsoup4 httpx
   ```
4. **Configure MCP Client**:
   Add the following to your MCP client configuration (e.g., Claude Desktop):
   ```json
   "airbnb-mcp-server": {
       "command": "uv",
       "args": [
           "--directory",
           "YOUR_CLONED_FOLDER",
           "run",
           "main.py"
       ]
   }
   ```
   Replace `YOUR_CLONED_FOLDER` with the path to the cloned repository.

## Remote MCP Server Configuration
The Airbnb Scraper MCP Server is hosted remotely at [https://smithery.ai/server/@alan5543/airbnb-scraper](https://smithery.ai/server/@alan5543/airbnb-scraper). To use it:
1. Visit [https://smithery.ai](https://smithery.ai) and sign in or create an account.
2. Go to the server page: [https://smithery.ai/server/@alan5543/airbnb-scraper](https://smithery.ai/server/@alan5543/airbnb-scraper).
3. Click "Add to Client" or follow Smithery.ai's integration instructions.
4. Update your MCP client (e.g., Claude Desktop) to use the remote server URL. Check your client's documentation for details on configuring remote MCP servers.
5. Test the connection to confirm the server is accessible and working.