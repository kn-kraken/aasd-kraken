import flet as ft
from geopy.geocoders import Nominatim

def main(page: ft.Page):
    page.title = "Apartment Listing Application"
    page.window.width = 1000
    page.window.height = 800

    # Initialize map coordinates as nonlocal variables
    coordinates = {
        "lat": 52.2297700,
        "lng": 21.0117800
    }
    
    # Initialize geocoder
    geolocator = Nominatim(user_agent="my_app")

    def search_location():
        try:
            # Combine address fields (excluding apartment number for search)
            address_parts = []
            if street.value:
                address_parts.append(street.value)
            if city.value:
                address_parts.append(city.value)
            
            full_address = ", ".join(address_parts)
            
            if full_address:
                location_data = geolocator.geocode(full_address)
                if location_data:
                    coordinates["lat"] = location_data.latitude
                    coordinates["lng"] = location_data.longitude
                    
                    # Parse address components
                    address_components = location_data.address.split(", ")
                    if(not address_components[0][0].isdigit() and address_components[1][0].isdigit()):
                        address_components = address_components[1:]
                    
                    # Clear previous values
                    verified_street.value = ""
                    verified_apartment.value = local_number.value if local_number.value else ""
                    verified_voivodeship.value = ""
                    verified_postal.value = ""
                    verified_country.value = ""
                    
                    # Set values based on address components
                    if address_components[0]:
                        verified_street.value = address_components[1] + " " + address_components[0]  # Street name and number
                    
                    # Find and set voivodeship (usually near the end, before country)
                    for comp in address_components:
                        if "województwo" in comp.lower():
                            verified_voivodeship.value = comp
                            break
                    
                    # Set postal code if found
                    for comp in address_components[1:]:
                        if any(c.isdigit() for c in comp) and len(comp) <= 10:
                            verified_postal.value = comp
                            break
                    
                    # Country is usually the last component
                    verified_country.value = address_components[-1]
                    
                    page.update()
                else:
                    page.overlay.append(ft.SnackBar(content=ft.Text("Location not found!")))
                    page.update()
        except Exception as e:
            page.overlay.append(ft.SnackBar(content=ft.Text(f"Error searching location: {str(e)}")))
            page.update()

    def open_map():
        try:
            url = f"https://www.openstreetmap.org/?mlat={coordinates['lat']}&mlon={coordinates['lng']}#map=15/{coordinates['lat']}/{coordinates['lng']}"
            import webbrowser
            webbrowser.open(url)
        except Exception as e:
            page.overlay.append(ft.SnackBar(content=ft.Text("Error opening map!")))
            page.update()

    # Function to handle form submission
    def submit_form():
        if (verified_street.value and price.value and description.value):
            # Combine address components for display
            address_parts = [
                verified_street.value,
                f"Apartment {verified_apartment.value}" if verified_apartment.value else "",
                verified_postal.value,
                verified_voivodeship.value,
                verified_country.value
            ]
            # Filter out empty parts
            full_address = ", ".join([part for part in address_parts if part])
            
            # Display the entered information
            listings.controls.append(
                ft.Card(
                    content=ft.Column([
                        ft.Text(f"Location: {full_address}", size=20, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Price: ${price.value}", size=16),
                        ft.Text(f"Description: {description.value}"),
                    ], spacing=10),
                    width=500,
                )
            )
            # Clear the form fields
            street.value = ""
            city.value = ""
            local_number.value = ""
            verified_street.value = ""
            verified_apartment.value = ""
            verified_voivodeship.value = ""
            verified_postal.value = ""
            verified_country.value = ""
            price.value = ""
            description.value = ""
            page.update()
        else:
            page.overlay.append(ft.SnackBar(content=ft.Text("All fields are required!")))
            page.update()

    # Form elements - Input fields
    street = ft.TextField(
        label="Street Address or Location Name", 
        hint_text="Enter street name and number", 
        width=400,
    )
    
    local_number = ft.TextField(
        label="Apartment Number (optional)",
        hint_text="Enter apartment/local number",
        width=190,
    )
    
    city = ft.TextField(
        label="City (optional)",
        hint_text="Enter city",
        width=190,
    )

    # Verified address fields
    verified_street = ft.TextField(
        label="Street",
        width=400,
        read_only=True
    )
    
    verified_apartment = ft.TextField(
        label="Apartment",
        width=240,
        read_only=True
    )
    
    verified_voivodeship = ft.TextField(
        label="Voivodeship",
        width=240,
        read_only=True
    )
    
    verified_postal = ft.TextField(
        label="Postal Code",
        width=190,
        read_only=True
    )
    
    verified_country = ft.TextField(
        label="Country",
        width=190,
        read_only=True
    )

    price = ft.TextField(
        label="Price (USD)", 
        hint_text="Enter the price", 
        width=400, 
        keyboard_type=ft.KeyboardType.NUMBER
    )
    
    description = ft.TextField(
        label="Description", 
        hint_text="Enter a brief description", 
        multiline=True, 
        width=400
    )

    # Buttons for location
    location_buttons = ft.Row([
        ft.ElevatedButton("Search Location", on_click=lambda _: search_location()),
        ft.ElevatedButton("View on Map", on_click=lambda _: open_map(), icon=ft.icons.MAP)
    ])

    # Button to submit form
    submit_button = ft.ElevatedButton("Add Listing", on_click=lambda _: submit_form(), width=200)

    # Container to display the list of apartments
    listings = ft.Column(spacing=20, scroll=True)

    # Main layout
    page.add(
        ft.Column([
            ft.Text("Apartment Listing Application", size=30, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            street,
            ft.Row([city, local_number], alignment=ft.MainAxisAlignment.START),
            location_buttons,
            verified_street,
            ft.Row([verified_apartment, verified_postal], alignment=ft.MainAxisAlignment.START),
            ft.Row([verified_voivodeship, verified_country], alignment=ft.MainAxisAlignment.START),
            price,
            description,
            submit_button,
            ft.Divider(),
            ft.Text("Apartment Listings:", size=24, weight=ft.FontWeight.W_600),
            listings,
        ], spacing=15)
    )

ft.app(target=main)