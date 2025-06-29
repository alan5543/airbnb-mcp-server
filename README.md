# Airbnb MCP Server

This Model Context Protocol (MCP) server provides tools to interact with Airbnb listings, allowing Large Language Models (LLMs) to search for accommodations and retrieve detailed information about specific listings.

## Tools Provided

1.  **`search_airbnb_listings(place, checkin_date, checkout_date, adults=1, children=0, infants=0, pets=0, price_max=1000, max_pages=3)`**
    * **Description:** Scrapes Airbnb listings for a given location and dates. Returns a JSON string of detailed listing information including price, rating, host details, and (after fetching individual page details) beds, bedrooms, bathrooms, and amenities.
    * **Parameters:**
        * `place` (string, required): The location name (e.g., "Hong Kong", "Toronto").
        * `checkin_date` (string, required): Check-in date in `YYYY-MM-DD` format (e.g., "2025-08-01").
        * `checkout_date` (string, required): Check-out date in `YYYY-MM-DD` format (e.g., "2025-08-06").
        * `adults` (integer, default: 1): Number of adults.
        * `children` (integer, default: 0): Number of children.
        * `infants` (integer, default: 0): Number of infants.
        * `pets` (integer, default: 0): Number of pets.
        * `price_max` (integer, default: 1000): Maximum price per night.
        * `max_pages` (integer, default: 3): Maximum number of search result pages to scrape.

2.  **`scrape_airbnb_listing_info(url, max_retries=3)`**
    * **Description:** Scrapes comprehensive information from a single Airbnb listing URL, providing a structured text summary including description, location, host, ratings, house rules, pricing, and image info.
    * **Parameters:**
        * `url` (string, required): The full Airbnb listing URL (e.g., "https://www.airbnb.ca/rooms/15956982?check_in=2025-08-01&check_out=2025-08-06&guests=1&adults=1").
        * `max_retries` (integer, default: 3): Number of attempts to fetch the HTML content.

## Local Setup and Running

To run this MCP server locally, you will need:

* Python 3.10 or higher installed.
* `uv` (a fast Python package installer and virtual environment manager). You can install it with:
    ```bash
    # On MacOS/Linux
    curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh
    # On Windows (PowerShell)
    powershell -ExecutionPolicy ByPass -c "irm [https://astral.sh/uv/install.ps1](https://astral.sh/uv/install.ps1) | iex"
    ```
    Remember to restart your terminal after installing `uv` for it to be in your PATH.

**Installation Steps:**

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/YourGitHubUsername/airbnb-mcp-server.git](https://github.com/YourGitHubUsername/airbnb-mcp-server.git)
    cd airbnb-mcp-server
    ```
    (Replace `YourGitHubUsername` with your actual GitHub username.)

2.  **Create and activate a virtual environment:**
    ```bash
    uv venv
    source .venv/bin/activate # For MacOS/Linux
    # Or for Windows PowerShell:
    # .venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    uv add -r requirements.txt
    ```

4.  **Run the MCP server:**
    ```bash
    /PATH/TO/YOUR/UV/uv run main.py
    ```
    (Replace `/PATH/TO/YOUR/UV/uv` with the actual full path to your `uv` executable, e.g., `/Users/alanyang/.local/bin/uv`)

## Connecting to an MCP Client (e.g., Claude for Desktop)

Once your server is running locally, you can connect an MCP client to it. For Claude for Desktop:

1.  Ensure Claude for Desktop is installed and updated.
2.  Open your Claude for Desktop configuration file:
    * **MacOS/Linux:** `~/Library/Application Support/Claude/claude_desktop_config.json`
    * **Windows:** `$env:AppData\Claude\claude_desktop_config.json`
3.  Add the following configuration to the `mcpServers` key. **Remember to replace `/PATH/TO/YOUR/UV/uv` with the actual full path to `uv` and `/ABSOLUTE/PATH/TO/airbnb_mcp_server` with the absolute path to your project folder.**

    ```json
    {
      "mcpServers": {
        "airbnb-scraper": {
          "command": "/PATH/TO/YOUR/UV/uv",
          "args": [
            "--directory",
            "/ABSOLUTE/PATH/TO/airbnb_mcp_server",
            "run",
            "main.py"
          ]
        }
      }
    }
    ```
4.  Save the file and restart Claude for Desktop.

## Logging

The server logs activity to `scraper.log` in the project directory. HTML content of scraped pages is saved to `debug_airbnb_page.html` for debugging.

## Contributing

Feel free to open issues or submit pull requests on the [GitHub repository](https://github.com/YourGitHubUsername/airbnb-mcp-server).