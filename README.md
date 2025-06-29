# Airbnb MCP Server

An MCP (Model Context Protocol) server for scraping and searching Airbnb listings. This server provides tools that can be connected to Large Language Models (LLMs) and other AI agents to fetch real-time data from Airbnb.

**Disclaimer:** This project is for educational purposes. Web scraping Airbnb is against their Terms of Service. The structure of Airbnb's website changes frequently, which can break this scraper at any time. Use at your own risk.

---

## Features

This server exposes two primary tools:

1.  `search_airbnb_listings`: Searches for listings based on location, dates, and number of guests, returning a detailed JSON list of properties.
2.  `scrape_airbnb_listing_info`: Fetches comprehensive details for a single Airbnb listing URL.

## Prerequisites

* Python 3.9+
* Git

## Installation and Local Setup

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/airbnb-mcp-server.git](https://github.com/YOUR_USERNAME/airbnb-mcp-server.git)
    cd airbnb-mcp-server
    ```

2.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## How to Run the MCP Server

You can run the server locally to test it. It will communicate over standard input/output (stdio), which is a common way for local agent frameworks to interact with it.

```bash
python main.py
```

The server is now running and waiting for MCP requests on stdio.

## Configuration for an LLM Agent

To allow an LLM to use your tools, you must provide it with the server's **schema**. The schema describes the available tools, their parameters, and what they return.

1.  **Get the Schema:**
    Run the following command in your terminal:
    ```bash
    mcp schema main:mcp
    ```

2.  **Use the Schema:**
    The output of this command is a JSON object. This JSON is what you provide to your LLM or agent framework. For example, when configuring a custom GPT in OpenAI, you would paste this schema into the designated area.

    This schema allows the LLM to understand how to call your `search_airbnb_listings` and `scrape_airbnb_listing_info` tools correctly.