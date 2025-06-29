import logging
import requests
from bs4 import BeautifulSoup
import json
import re
import base64
import urllib.parse
from typing import Any, List, Dict
import asyncio
from urllib.parse import urlparse, parse_qs
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, filename='scraper.log', format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from mcp.server.fastmcp import FastMCP
import httpx

mcp = FastMCP("airbnb-scraper")

BASE_AIRBNB_ROOM_URL = "https://www.airbnb.ca/rooms/"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

async def get_page_html_async(url: str) -> str | None:
    """
    Fetches the HTML content from a given URL asynchronously.
    """
    logger.info(f"Fetching HTML from: {url}")
    headers = {
        'User-Agent': USER_AGENT,
        'Accept-Language': 'en-US,en;q=0.9',
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            html_content = response.text

            # with open("debug_airbnb_page.html", "w", encoding="utf-8") as f:
            #     f.write(html_content)
            # logger.info("Saved current page HTML to debug_airbnb_page.html for inspection.")

            return html_content
    except httpx.RequestError as e:
        logger.error(f"Error fetching the URL {url}: {e}")
        return None
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching {url}: {e.response.status_code}. The server might be blocking requests.")
        return None

async def scrape_listing_details(listing_id: str) -> Dict[str, Any]:
    """
    Scrapes additional details from an individual listing page.
    """
    url = f"{BASE_AIRBNB_ROOM_URL}{listing_id}"
    logger.info(f"Scraping details for listing {listing_id}")
    html_content = await get_page_html_async(url)
    details = {
        'beds': 'N/A',
        'bedrooms': 'N/A',
        'bathrooms': 'N/A',
        'amenities': [],
        'location': 'N/A'
    }

    if not html_content:
        logger.error(f"Failed to fetch details for listing {listing_id}")
        return details

    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        script_element = soup.find('script', id="data-deferred-state-0")
        if not (script_element and script_element.string):
            logger.error(f"No data-deferred-state-0 script found for listing {listing_id}")
            return details

        full_data = json.loads(script_element.string)
        client_data = full_data.get("niobeMinimalClientData", [])
        if not client_data or len(client_data) < 1 or len(client_data[0]) < 2:
            logger.error(f"Unexpected JSON structure for listing {listing_id}")
            return details

        listing_data = client_data[0][1].get('data', {}).get('presentation', {}).get('stayProductDetail', {})
        section_data = listing_data.get('sections', {})

        # Extract beds, bedrooms, bathrooms
        for section in section_data.get('sectionData', []):
            if section.get('sectionType') == 'HIGHLIGHTS':
                highlights = section.get('sectionItems', [])
                for highlight in highlights:
                    title = highlight.get('title', '').lower()
                    if 'bed' in title and 'bedroom' not in title:
                        details['beds'] = highlight.get('subtitle', 'N/A')
                    elif 'bedroom' in title:
                        details['bedrooms'] = highlight.get('subtitle', 'N/A')
                    elif 'bath' in title:
                        details['bathrooms'] = highlight.get('subtitle', 'N/A')

        # Extract amenities
        amenities_section = next((s for s in section_data.get('sectionData', []) if s.get('sectionType') == 'AMENITIES'), {})
        details['amenities'] = [item.get('title', 'N/A') for item in amenities_section.get('sectionItems', [])]

        # Extract location
        location_section = next((s for s in section_data.get('sectionData', []) if s.get('sectionType') == 'LOCATION'), {})
        details['location'] = location_section.get('title', 'N/A')

    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logger.error(f"Error processing listing details for {listing_id}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error processing listing details for {listing_id}: {e}")

    return details

async def extract_room_information(html_content: str, checkin_date: str, checkout_date: str, adults: int, guests: int) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Extracts room information and pagination data from the Airbnb page's JSON payload.
    Always fetches additional details from individual listing pages.

    Args:
        html_content (str): HTML content of the Airbnb search results page.
        checkin_date (str): Check-in date in YYYY-MM-DD format.
        checkout_date (str): Check-out date in YYYY-MM-DD format.
        adults (int): Number of adults.
        guests (int): Total number of guests.

    Returns:
        tuple: (list of room information dictionaries, pagination information dictionary)
    """
    listings_data = []
    pagination_info = {}

    # Parse HTML and find script tag
    soup = BeautifulSoup(html_content, 'html.parser')
    script_element = soup.find('script', id="data-deferred-state-0")
    if not script_element or not script_element.string:
        logger.error("Script tag 'data-deferred-state-0' not found or empty.")
        return [], {}

    # Parse JSON from script tag
    try:
        full_data = json.loads(script_element.string)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from script tag: {e}")
        return [], {}

    # Access niobeMinimalClientData
    client_data = full_data.get("niobeMinimalClientData", [])

    if not client_data or not isinstance(client_data, list) or len(client_data) < 1 or len(client_data[0]) < 2:
        logger.error("'niobeMinimalClientData' is missing or has unexpected structure.")
        return [], {}

    # Access relevant data
    relevant_data = client_data[0][1]
    if not isinstance(relevant_data, dict):
        logger.error("'niobeMinimalClientData[0][1]' is not a dictionary.")
        return [], {}

    # Navigate to staysSearch.results
    data = relevant_data.get('data')
    if data is None:
        logger.error("'data' key missing in JSON payload.")
        return [], {}

    presentation = data.get('presentation')
    if presentation is None:
        logger.error("'presentation' key missing in JSON payload.")
        return [], {}

    stays_search = presentation.get('staysSearch')
    if stays_search is None:
        logger.error("'staysSearch' key missing in JSON payload.")
        return [], {}

    results = stays_search.get('results')
    if results is None:
        logger.error("'results' key missing in JSON payload.")
        return [], {}

    # Extract pagination info and search results
    pagination_info = results.get('paginationInfo', {})
    search_results = results.get('searchResults', [])
    if not search_results:
        logger.warning("No 'searchResults' found in JSON payload.")
        return [], pagination_info

    # Process each listing
    for index, listing in enumerate(search_results):
        try:
            if not isinstance(listing, dict):
                logger.warning(f"Listing at index {index} is not a dictionary, skipping.")
                continue

            room_info = {}
            demand_stay_listing = listing.get('demandStayListing', {})
            structured_content = listing.get('structuredContent', {})
            passport_data = listing.get('passportData', {})

            # Extract listing ID and URL
            listing_id = "N/A"
            listing_id_encoded = demand_stay_listing.get('id')
            if listing_id_encoded:
                try:
                    decoded_id_string = base64.b64decode(listing_id_encoded).decode('utf-8')
                    listing_id = decoded_id_string.split(':')[-1]
                    room_info['listing_id'] = listing_id
                    # Modified line to include detailed query parameters
                    room_info['url'] = f"{BASE_AIRBNB_ROOM_URL}{listing_id}?check_in={checkin_date}&check_out={checkout_date}&guests={guests}&adults={adults}"
                except (base64.binascii.Error, UnicodeDecodeError, IndexError) as e:
                    logger.error(f"Error decoding listing ID {listing_id_encoded} at index {index}: {e}")
                    room_info['listing_id'] = 'N/A'
                    room_info['url'] = 'N/A'

            # Extract title
            description = demand_stay_listing.get('description', {})
            name = description.get('name', {})
            room_info['title'] = name.get('localizedStringWithTranslationPreference', 'N/A')

            # Extract price
            structured_display_price = listing.get('structuredDisplayPrice', {})
            primary_line = structured_display_price.get('primaryLine', {})
            room_info['price'] = primary_line.get('accessibilityLabel', 'N/A')
            room_info['price_qualifier'] = primary_line.get('qualifier', 'N/A')

            # Extract rating
            room_info['average_rating'] = listing.get('avgRatingA11yLabel', 'N/A')
            room_info['rating_count'] = passport_data.get('ratingCount', 0)

            # Extract host info
            room_info['host_name'] = passport_data.get('name', 'N/A')
            room_info['host_is_verified'] = passport_data.get('isVerified', False)
            room_info['host_is_superhost'] = passport_data.get('isSuperhost', False)
            time_as_host = passport_data.get('timeAsHost', {})
            room_info['host_years'] = time_as_host.get('years', 0)
            room_info['host_months'] = time_as_host.get('months', 0)

            # Extract location
            location = demand_stay_listing.get('location', {})
            coordinate = location.get('coordinate', {})
            room_info['latitude'] = coordinate.get('latitude', 'N/A')
            room_info['longitude'] = coordinate.get('longitude', 'N/A')

            # Extract beds and guests
            beds_info = 'N/A'
            guests_info = 'N/A'
            secondary_line = structured_content.get('secondaryLine', [])
            for item in secondary_line:
                body_text = item.get('body', '')
                bed_match = re.search(r'(\d+\s*bed(s)?)', body_text, re.IGNORECASE)
                if bed_match:
                    beds_info = bed_match.group(1)
                guest_match = re.search(r'(\d+\s*guest(s)?)', body_text, re.IGNORECASE)
                if guest_match:
                    guests_info = guest_match.group(1)
            room_info['beds'] = beds_info
            room_info['guests'] = guests_info

            # Extract images
            contextual_pictures = listing.get('contextualPictures', [])
            room_info['image_urls'] = [img.get('picture', 'N/A') for img in contextual_pictures]

            # Extract badges
            room_info['badges'] = [badge.get('id', 'N/A') for badge in listing.get('badges', [])]

            # Extract listing type
            listing_type = 'N/A'
            for item in structured_content.get('distance', []) + structured_content.get('mapCategoryInfo', []):
                if item.get('type') == 'LISTING_PRIVATE_ROOM_SUITE_HIGHLIGHT':
                    listing_type = 'Private Room'
                    break
            room_info['listing_type'] = listing_type

            # Initialize additional fields
            room_info['bedrooms'] = 'N/A'
            room_info['bathrooms'] = 'N/A'
            room_info['amenities'] = []
            room_info['location'] = 'N/A'

            listings_data.append(room_info)

        except Exception as e:
            logger.error(f"Error processing listing at index {index}: {e}")
            continue

    # Always fetch additional details
    if listings_data:
        logger.info(f"Fetching details for {len(listings_data)} listings")
        tasks = [scrape_listing_details(room['listing_id']) for room in listings_data if room['listing_id'] != 'N/A']
        details_list = await asyncio.gather(*tasks, return_exceptions=True)
        for room, details in zip(listings_data, details_list):
            if isinstance(details, dict):
                if details['beds'] != 'N/A':
                    room['beds'] = details['beds']
                if details['bedrooms'] != 'N/A':
                    room['bedrooms'] = details['bedrooms']
                if details['bathrooms'] != 'N/A':
                    room['bathrooms'] = details['bathrooms']
                room['amenities'] = details['amenities']
                room['location'] = details['location']
            else:
                logger.warning(f"Failed to fetch details for listing {room['listing_id']}: {details}")

    return listings_data, pagination_info

@mcp.tool()
async def search_airbnb_listings(
    place: str,
    checkin_date: str,
    checkout_date: str,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    pets: int = 0,
    price_max: int = 1000,
    max_pages: int = 3
) -> str:
    """
    Scrapes Airbnb listings for a given location and dates, returning detailed information for each listing.
    Always fetches details from individual listing pages to include beds, bedrooms, bathrooms, amenities, and location.
    Optimized for Telegram with concise output and sanitized titles.

    Args:
        place: The location name, Please use the English name of the location (e.g., "Hong Kong").
        checkin_date: The check-in date in YYYY-MM-DD format (e.g., "2025-08-01").
        checkout_date: The check-out date in YYYY-MM-DD format (e.g., "2025-08-06").
        adults: Number of adults (default: 1).
        children: Number of children (default: 0).
        infants: Number of infants (default: 0).
        pets: Number of pets (default: 0).
        price_max: Maximum price per night (you must ask the user to provide how is their budget).
        max_pages: Maximum number of pages to scrape (default: 3).

    Returns:
        str: JSON string containing a list of listings, each with:
            - listing_id: Unique listing identifier
            - url: Direct link to the Airbnb listing
            - title: Listing title (sanitized, max 50 characters)
            - price: Price per night or total (e.g., "$39 CAD per night")
            - price_qualifier: Additional price context (e.g., "per night")
            - average_rating: Rating (e.g., "4.78") or "N/A"
            - rating_count: Number of reviews
            - host_name: Host's first name
            - host_is_verified: Whether host is verified
            - host_is_superhost: Whether host is a superhost
            - host_years: Years as host
            - host_months: Months as host
            - latitude: Listing latitude
            - longitude: Listing longitude
            - beds: Number of beds (e.g., "2 beds")
            - guests: Number of guests (e.g., "4 guests")
            - bedrooms: Number of bedrooms (e.g., "2 bedrooms")
            - bathrooms: Number of bathrooms (e.g., "1 bath")
            - amenities: List of amenities (e.g., ["Wi-Fi", "Kitchen"])
            - location: Neighborhood or specific location
            - image_urls: List of image URLs
            - badges: List of badges (e.g., ["NEW"])
            - listing_type: Type of listing (e.g., "Private Room")
        If no listings are found, returns a plain-text error message.
    """
    # Validate inputs
    current_year = datetime.now().year  # Dynamically get the current year

    # Validate and adjust checkin_date
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", checkin_date):
        return "Invalid check-in date format: Must be YYYY-MM-DD."
    try:
        cin_date = datetime.strptime(checkin_date, "%Y-%m-%d")
        if cin_date.year < current_year:
            checkin_date = f"{current_year}-{cin_date.strftime('%m-%d')}"
            logger.info(f"Adjusted checkin_date from {cin_date.year} to {current_year}: {checkin_date}")
    except ValueError:
        return "Invalid check-in date: Unable to parse date."

    # Validate and adjust checkout_date
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", checkout_date):
        return "Invalid check-out date format: Must be YYYY-MM-DD."
    try:
        cout_date = datetime.strptime(checkout_date, "%Y-%m-%d")
        if cout_date.year < current_year:
            checkout_date = f"{current_year}-{cout_date.strftime('%m-%d')}"
            logger.info(f"Adjusted checkout_date from {cout_date.year} to {current_year}: {checkout_date}")
    except ValueError:
        return "Invalid check-out date: Unable to parse date."

    # Compute total guests
    guests = adults + children + infants
    # URL-encode the place string
    encoded_place = urllib.parse.quote(place)
    logger.info(f"Starting scrape for place: {place} (encoded: {encoded_place})")

    initial_url_template = (
        "https://www.airbnb.ca/s/{encoded_place}/homes?"
        "refinement_paths%5B%5D=%2Fhomes"
        "&date_picker_type=calendar"
        "&checkin={checkin_date}"
        "&checkout={checkout_date}"
        "&adults={adults}"
        "&children={children}"
        "&infants={infants}"
        "&pets={pets}"
        "&source=structured_search_input_header"
    )

    if price_max is not None:
        initial_url_template += "&price_max={price_max}"

    initial_url = initial_url_template.format(
        encoded_place=encoded_place,
        checkin_date=checkin_date,
        checkout_date=checkout_date,
        adults=adults,
        children=children,
        infants=infants,
        pets=pets,
        **({'price_max': price_max} if price_max is not None else {})
    )
    
    all_rooms = []
    current_url = initial_url
    page_count = 0

    while current_url and page_count < max_pages:
        page_count += 1
        logger.info(f"Scraping page {page_count}: {current_url}")
        html_content = await get_page_html_async(current_url)

        if html_content is None:
            logger.error(f"Failed to retrieve HTML for page {page_count}. Stopping scrape.")
            break

        # Pass search parameters to extract_room_information
        rooms_on_page, pagination_data = await extract_room_information(
            html_content, checkin_date, checkout_date, adults, guests
        )
        
        if rooms_on_page:
            all_rooms.extend(rooms_on_page)
            logger.info(f"Extracted {len(rooms_on_page)} rooms from page {page_count}")
        else:
            logger.warning(f"No rooms found on page {page_count}. This might indicate the end of the results.")
            if page_count == 1:
                break
        
        next_cursor_str = pagination_data.get('nextPageCursor')
        if next_cursor_str:
            parsed_initial_url = urllib.parse.urlparse(initial_url)
            query_params = urllib.parse.parse_qs(parsed_initial_url.query)
            query_params['cursor'] = [next_cursor_str]
            
            next_page_query = urllib.parse.urlencode(query_params, doseq=True)
            current_url = parsed_initial_url._replace(query=next_page_query).geturl()
            logger.info(f"Next page cursor found. Updating URL for page {page_count + 1}")
        else:
            logger.info("No 'nextPageCursor' found. Reached the last page or an error occurred.")
            current_url = None
    
    logger.info(f"Scraping complete. Total rooms extracted: {len(all_rooms)}")

    # Deduplicate listings by listing_id
    unique_rooms = {room['listing_id']: room for room in all_rooms if room['listing_id'] != 'N/A'}
    all_rooms = list(unique_rooms.values())
    logger.info(f"Total unique rooms after deduplication: {len(all_rooms)}")

    if all_rooms:
        return json.dumps(all_rooms, indent=2, ensure_ascii=False)
    else:
        logger.warning("No Airbnb listings found for the given criteria, or the scraper was blocked.")
        return "No Airbnb listings found for the given criteria, or the scraper was blocked. Check the debug_airbnb_page.html file for details."


@mcp.tool()
async def scrape_airbnb_listing_info(url: str, max_retries: int = 3) -> str:
    """
    Scrapes comprehensive information from a single Airbnb listing URL, including title, location, host, price, ratings, amenities, policies, and booking parameters, returning a structured text summary.

    Args:
        url: The Airbnb listing URL, including optional query parameters like check_in, check_out, guests, and adults (e.g., "https://www.airbnb.ca/rooms/15956982?check_in=2025-08-01&check_out=2025-08-06&guests=1&adults=1").
        max_retries: Number of attempts to fetch the HTML content if the initial request fails (default: 3).

    Returns:
        A information string containing a structured summary of the Airbnb Description, Location, Host, Rating and Reviews, House Rules, Prices Info, and Image Info.
    """
    logger.info(f"Fetching details for listing URL: {url}")
    
    # Parse URL and extract query parameters
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    check_in = query_params.get('check_in', ['N/A'])[0]
    check_out = query_params.get('check_out', ['N/A'])[0]
    guests = query_params.get('guests', ['N/A'])[0]
    adults = query_params.get('adults', ['N/A'])[0]

    # Extract listing_id from URL
    match = re.search(r'/rooms/(\d+)', url)
    if not match:
        logger.error(f"Invalid Airbnb URL: {url}")
        return "Invalid Airbnb URL provided."
    
    listing_id = match.group(1)
    
    # Retry fetching HTML
    for attempt in range(max_retries):
        html_content = await get_page_html_async(url)
        if html_content:
            break
        logger.warning(f"Retry {attempt + 1}/{max_retries} for listing {listing_id}")
        await asyncio.sleep(1)
    else:
        logger.error(f"Failed to fetch HTML for listing {listing_id} after {max_retries} attempts")
        return f"Failed to fetch details for listing {listing_id} after {max_retries} retries."

    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        script_element = soup.find('script', id="data-deferred-state-0")
        if not (script_element and script_element.string):
            logger.error(f"No data-deferred-state-0 script found for listing {listing_id}")
            return f"No data found for listing {listing_id}."

        full_data = json.loads(script_element.string)
        client_data = full_data.get("niobeMinimalClientData", [])
        if not client_data or not isinstance(client_data, list) or len(client_data) < 1 or len(client_data[0]) < 2:
            logger.error("'niobeMinimalClientData' is missing or has unexpected structure.")
            return f"No valid data found for listing {listing_id}."
        
        logger.info("client_data")
        relevant_data = client_data[0][1]
        if not isinstance(relevant_data, dict):
            logger.error("'niobeMinimalClientData[0][1]' is not a dictionary.")
            return f"Invalid data structure for listing {listing_id}."
            
        logger.info("relevant_data")
        data = relevant_data.get('data')
        if data is None:
            logger.error("'data' key missing in JSON payload.")
            return f"No data found for listing {listing_id}."

        logger.info("data")

        presentation = data.get('presentation', {}).get('stayProductDetailPage', {}).get('sections', {})
        sections = presentation.get('sections', [])

        # Initialize variables to store extracted details
        listing_details: Dict[str, Any] = {
            'airbnb_description': 'N/A',
            'airbnb_location': 'N/A',
            'airbnb_host': 'N/A',
            'airbnb_rating_and_reviews': 'N/A',
            'airbnb_house_rules': 'N/A',
            'airbnb_prices_info': 'N/A',
            'airbnb_image_info': 'N/A'
        }

        # Iterate through sections to extract relevant information
        for section_container in sections:
            section = section_container.get('section', {})
            section_type = section_container.get('sectionComponentType')

            # Title and description
            if section_type == 'PDP_DESCRIPTION_MODAL':
                listing_details['airbnb_description'] = section

            # Location and coordinates
            if section_type == 'LOCATION_PDP':
                listing_details['airbnb_location'] = section

            # Host details
            if section_type == 'MEET_YOUR_HOST':
                listing_details['airbnb_location'] = section

            # Rating and reviews
            if section_type == 'REVIEWS_DEFAULT':
                listing_details['airbnb_host'] = section

            # House rules and safety info
            if section_type == 'POLICIES_DEFAULT':
                listing_details['airbnb_house_rules'] = section

            # Price, capacity, and listing type
            if section_type in ['BOOK_IT_SIDEBAR', 'BOOK_IT_FLOATING_FOOTER']:
                listing_details['airbnb_prices_info'] = section

            # Images and badges
            if section_type == 'HERO_DEFAULT':
                listing_details['airbnb_image_info'] = section

        # Format the output string
        output = f"""
        # Airbnb Info
        {listing_details['airbnb_description']}
        # Airbnb Location:
        {listing_details['airbnb_location']}
        # Airbnb Host:
        {listing_details['airbnb_host']}
        # Airbnb Rating and Reviews:
        {listing_details['airbnb_rating_and_reviews']}
        # Airbnb House Rules:
        {listing_details['airbnb_house_rules']}
        # Airbnb Prices Info:
        {listing_details['airbnb_prices_info']}
        # Airbnb Image Info:
        {listing_details['airbnb_image_info']}
        """

        return output

    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logger.error(f"Error processing listing details for {listing_id}: {e}")
        return f"Error processing details for listing {listing_id}."
    except Exception as e:
        logger.error(f"Unexpected error processing listing {listing_id}: {e}")
        return f"Unexpected error for listing {listing_id}."



if __name__ == "__main__":
    logger.info("Starting Airbnb MCP server...")
    mcp.run(transport='stdio')
    logger.info("Airbnb MCP server stopped.")