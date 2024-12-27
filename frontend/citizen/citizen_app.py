import flet as ft
import sys
import os
import asyncio
from geopy.geocoders import Nominatim

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'database')))

from agents.citizen.main import run_citizen_agent, ServiceDemand
from system_data import SERVICE_OPTIONS, PREMISE_DEMAND_PRIORITY

def main(page: ft.Page):
    page.title = "Service Request Form"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.window.width = 1000
    page.window.height = 800

    # Initialize map coordinates
    coordinates = {
        "lat": 52.2297700,
        "lng": 21.0117800
    }
    
    # Initialize geocoder
    geolocator = Nominatim(user_agent="citizen_app")

    name_input = ft.TextField(label="Full Name", autofocus=True)
    street = ft.TextField(label="Street Name", hint_text="Enter street name", width=300)
    street_number = ft.TextField(label="Street Number", hint_text="Number", width=90)
    postal_code = ft.TextField(label="Postal Code (optional)", hint_text="Enter postal code", width=150)
    city = ft.TextField(label="City", hint_text="Enter city", width=190)
    
    # Verified address fields
    verified_address = ft.TextField(
        label="Verified Address", 
        width=600, 
        read_only=True,
        multiline=True,
        min_lines=2,
        text_size=16
    )
    
    service_input = ft.Dropdown(
        label="Service",
        options=[ft.dropdown.Option(name) for name in SERVICE_OPTIONS],
        width=400
    )
    
    priority_input = ft.Dropdown(
        label="Priority",
        options=[ft.dropdown.Option(priority) for priority in PREMISE_DEMAND_PRIORITY],
        width=400
    )
    
    description_input = ft.TextField(
        label="Request Description", 
        multiline=True, 
        min_lines=3, 
        max_lines=5,
        width=400
    )

    def validate_fields():
        # Check if all required fields are filled
        is_valid = all([
            name_input.value,
            verified_address.value,
            service_input.value,
            priority_input.value,
        ])
        # Enable/disable submit button based on validation
        submit_button.disabled = not is_valid
        page.update()

    # Add on_change handlers to all required fields
    name_input.on_change = lambda _: validate_fields()
    service_input.on_change = lambda _: validate_fields()
    priority_input.on_change = lambda _: validate_fields()
    description_input.on_change = lambda _: validate_fields()

    def search_location():
        try:
            address_parts = []
            if street.value:
                address_parts.append(street.value)
                if street_number.value:
                    address_parts[-1] += " " + street_number.value
            if postal_code.value:
                address_parts.append(postal_code.value)
            if city.value:
                address_parts.append(city.value)
            
            full_address = ", ".join(address_parts)
            
            if full_address:
                location_data = geolocator.geocode(full_address)
                if location_data:
                    coordinates["lat"] = location_data.latitude
                    coordinates["lng"] = location_data.longitude
                    verified_address.value = location_data.address
                    validate_fields()  # Add validation check after address verification
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

    def submit_form():
        service_demand = ServiceDemand(
            localization=[coordinates["lat"], coordinates["lng"]], 
            service_type=service_input.value, 
            priority=priority_input.value
        )
        
        run_citizen_agent(service_demand)

        # Clear all fields after successful submission
        name_input.value = ""
        street.value = ""
        street_number.value = ""
        postal_code.value = ""
        city.value = ""
        verified_address.value = ""
        service_input.value = None
        priority_input.value = None
        description_input.value = ""
        
        text = ft.Text("Thank you for submitting your request!")
        text.padding = ft.padding.all(20)
        page.add(text)
        validate_fields()  # Validate fields after clearing
        page.update()

    # Location buttons
    location_buttons = ft.Row([
        ft.ElevatedButton("Search Location", on_click=lambda _: search_location()),
        ft.ElevatedButton("View on Map", on_click=lambda _: open_map(), icon=ft.icons.MAP)
    ])

    submit_button = ft.ElevatedButton(
        "Submit Request",
        on_click=lambda _: submit_form(),
        disabled=True  # Start with disabled button
    )

    # Main layout
    page.add(
        ft.Column([
            ft.Text("Service Request Form", size=30, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            name_input,
            ft.Row([
                street,
                street_number,
                postal_code,
                city
            ], alignment=ft.MainAxisAlignment.START),
            location_buttons,
            verified_address,
            service_input,
            priority_input,
            description_input,
            submit_button
        ], spacing=15)
    )

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
ft.app(target=main)