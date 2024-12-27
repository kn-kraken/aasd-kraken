import flet as ft
from geopy.geocoders import Nominatim
import sys
import os
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'database')))
from system_data import SERVICE_OPTIONS


def main(page: ft.Page):
    page.title = "Rental Offer Application"
    page.window.width = 1000
    page.window.height = 1000
    page.scroll = "auto"

    def change_tab(e):
        tabs.selected_index = e.control.selected_index
        tab_content.content = tabs_content[e.control.selected_index]
        page.update()

    # Tabs for navigation
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text="Create Offer"),
            ft.Tab(text="View Offers"),
        ],
        on_change=change_tab,
    )

    offers = ft.Column(spacing=20, scroll=True)

    # View offers section
    offers_view = ft.Column([
        ft.Text("Rental Offers", size=30, weight=ft.FontWeight.BOLD),
        ft.Divider(),
        offers,
    ], scroll="auto")

    coordinates = {"lat": 52.2297700, "lng": 21.0117800}

    # Initialize geolocator
    geolocator = Nominatim(user_agent="rental_app")

    # Notes and error messages
    required_note = ft.Text(
        "* indicates required fields",
        size=12,
        color=ft.colors.GREY_700,
        italic=True
    )

    localization_error_text = ft.Text(visible=False, color=ft.colors.RED_400, size=12)
    price_error_text = ft.Text(visible=False, color=ft.colors.RED_400, size=12)

    # Form fields
    def validate_form():
        required_fields = [tenant_name, street, min_price, max_price]
        is_valid = all(field.value.strip() for field in required_fields) and validate_prices()
        submit_button.disabled = not is_valid
        page.update()

    tenant_name = ft.TextField(
        label="Your Full Name *", 
        hint_text="Enter your full name",
        width=400,
        on_change=lambda _: validate_form(),
    )

    street = ft.TextField(
        label="Street Address or Location Name *", 
        hint_text="Enter street name and number", 
        width=400,
        on_change=lambda _: validate_form(),
    )

    city = ft.TextField(
        label="City (optional)",
        hint_text="Enter city",
        width=190,
        on_change=lambda _: validate_form(),
    )

    verified_address = ft.TextField(
        label="Verified Address",
        width=400,
        read_only=True
    )

    min_price = ft.TextField(
        label="Minimum Price (USD) *", 
        hint_text="Enter the minimum price", 
        width=190, 
        keyboard_type=ft.KeyboardType.NUMBER,
        on_change=lambda _: validate_form(),
    )

    max_price = ft.TextField(
        label="Maximum Price (USD) *", 
        hint_text="Enter the maximum price", 
        width=190, 
        keyboard_type=ft.KeyboardType.NUMBER,
        on_change=lambda _: validate_form(),
    )

    service_options_dropdown = ft.Dropdown(
        label="Service Type",
        hint_text="Select one or more services",
        options=[ft.dropdown.Option(service) for service in SERVICE_OPTIONS],
        width=400,
    )

    service_options_container = ft.Container(
        content=ft.Column([
            ft.Text("Service Type", size=16, weight=ft.FontWeight.W_500),
            service_options_dropdown,
        ]),
        border=ft.border.all(1, ft.colors.BLACK45),
        border_radius=5,
        padding=10,
        width=400,
    )

    description = ft.TextField(
        label="Description (optional)", 
        hint_text="Enter a brief description", 
        multiline=True, 
        width=400
    )

    location_buttons = ft.Row([
        ft.ElevatedButton("Search Location", on_click=lambda _: search_location()),
        ft.ElevatedButton("View on Map", on_click=lambda _: open_map(), icon=ft.icons.MAP)
    ])

    submit_button = ft.ElevatedButton(
        "Submit Offer", 
        on_click=lambda _: submit_offer(), 
        width=200,
        disabled=True,
    )

    # Functions for validation and interaction
    def validate_prices():
        try:
            min_val = float(min_price.value) if min_price.value else 0
            max_val = float(max_price.value) if max_price.value else 0
            if min_val <= 0 or max_val <= 0 or min_val > max_val:
                price_error_text.value = "Ensure valid prices and Min <= Max"
                price_error_text.visible = True
                return False
            price_error_text.visible = False
            return True
        except ValueError:
            price_error_text.value = "Enter valid numeric values for prices"
            price_error_text.visible = True
            return False

    def search_location():
        try:
            address_parts = [street.value]
            if city.value.strip():  # Only include city if provided
                address_parts.append(city.value.strip())
            full_address = ", ".join([part for part in address_parts if part])

            if full_address:
                location_data = geolocator.geocode(full_address)
                if location_data:
                    coordinates["lat"] = location_data.latitude
                    coordinates["lng"] = location_data.longitude
                    verified_address.value = location_data.address
                    localization_error_text.visible = False
                else:
                    localization_error_text.value = "Location not found"
                    localization_error_text.visible = True
            else:
                localization_error_text.value = "Please enter a street address"
                localization_error_text.visible = True
        except Exception as e:
            localization_error_text.value = f"Error: {str(e)}"
            localization_error_text.visible = True

        page.update()

    def open_map():
        try:
            url = f"https://www.openstreetmap.org/?mlat={coordinates['lat']}&mlon={coordinates['lng']}#map=15/{coordinates['lat']}/{coordinates['lng']}"
            import webbrowser
            webbrowser.open(url)
        except Exception as e:
            page.overlay.append(ft.SnackBar(content=ft.Text("Error opening map!")))
            page.update()

    def submit_offer():
        if not validate_prices():
            page.overlay.append(ft.SnackBar(content=ft.Text("Fix price errors before submitting")))
            page.update()
            return

        address = verified_address.value or "[Unverified Address]"

        service = service_options_dropdown.value

        offers.controls.append(
            ft.Card(
                content=ft.Container(content=ft.Column([
                    ft.Text(f"Tenant: {tenant_name.value}", size=16, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Location: {address}", size=16),
                    ft.Text(f"Price Range: {min_price.value} PLN - {max_price.value} PLN", size=16),
                    ft.Text(f"Description: {description.value}", size=16),
                    ft.Text(f"Service Type: {service}" if service else "No specific services", size=16),
                ], spacing=10), padding=20),
                width=500,
            )
        )

        # Clear form
        tenant_name.value = ""
        street.value = ""
        city.value = ""
        verified_address.value = ""
        min_price.value = ""
        max_price.value = ""
        description.value = ""
        service_options_dropdown.value = []

        page.update()

    # Main form layout
    form_view = ft.Container(
        content=ft.Column([
            ft.Text("Create Rental Offer", size=30, weight=ft.FontWeight.BOLD),
            required_note,
            ft.Divider(),
            tenant_name,
            street,
            city,
            location_buttons,
            verified_address,
            localization_error_text,
            ft.Row([
                ft.Column([min_price]),
                ft.Column([max_price, price_error_text]),
            ]),
            service_options_container,
            description,
            submit_button,
        ], spacing=15),
        padding=20,
    )

    tabs_content = [form_view, offers_view]
    tab_content = ft.Container(
        content=tabs_content[0],
        padding=ft.padding.only(top=20)
    )

    page.add(
        ft.Column([
            tabs,
            tab_content
        ])
    )

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
ft.app(target=main)
