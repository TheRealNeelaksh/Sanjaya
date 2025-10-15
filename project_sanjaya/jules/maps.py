import folium
import os
from playwright.sync_api import sync_playwright

MAP_HTML_PATH = "logs/temp_trip_map.html"
MAP_IMAGE_PATH = "logs/final_trip_map.png"

def generate_trip_map(events):
    """
    Generates a Folium map from trip events and saves it as an HTML file.
    """
    if not events:
        return None

    # Separate ground and flight coordinates
    ground_coords = [(e['lat'], e['lon']) for e in events if e.get('source') == 'web']
    flight_coords = [(e['lat'], e['lon']) for e in events if e.get('source') == 'flight']

    # Create map centered on the last known point
    m = folium.Map(location=(events[-1]['lat'], events[-1]['lon']), zoom_start=6)

    # Add ground path
    if ground_coords:
        folium.PolyLine(ground_coords, color="#3498db", weight=5, opacity=0.8, popup="Ground Path").add_to(m)

    # Add flight path
    if flight_coords:
        folium.PolyLine(flight_coords, color="#f39c12", weight=4, opacity=0.9, dash_array='10, 5', popup="Flight Path").add_to(m)

    # Add markers for start and end
    folium.Marker(location=(events[0]['lat'], events[0]['lon']), popup="Trip Start", icon=folium.Icon(color='green', icon='play')).add_to(m)
    folium.Marker(location=(events[-1]['lat'], events[-1]['lon']), popup="Trip End", icon=folium.Icon(color='red', icon='stop')).add_to(m)

    # Auto-fit map bounds
    bounds = m.get_bounds()
    m.fit_bounds(bounds, padding=(50, 50))

    m.save(MAP_HTML_PATH)
    return MAP_HTML_PATH

def capture_map_screenshot(html_path):
    """
    Uses Playwright to take a screenshot of the generated map HTML file.
    """
    if not html_path or not os.path.exists(html_path):
        return None

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        # The path must be converted to a file URI
        page.goto(f"file://{os.path.abspath(html_path)}")
        # Wait for the map tiles to load
        page.wait_for_timeout(5000)
        page.screenshot(path=MAP_IMAGE_PATH, full_page=True)
        browser.close()

    # Clean up the temporary HTML file
    os.remove(html_path)

    print(f"Map image saved to {MAP_IMAGE_PATH}")
    return MAP_IMAGE_PATH