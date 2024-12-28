import flet as ft
from geopy.geocoders import Nominatim
import sys
import threading
import os
import asyncio
import spade

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'database')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from system_data import SERVICE_OPTIONS
from agents.premise_for_rent.main import RentalOfferDetails, PremiseForRentAgentInterface
SERVICE_OPTIONS = [opt for opt in SERVICE_OPTIONS if opt != "Other"]


event_queue = asyncio.Queue()
agent = PremiseForRentAgentInterface(event_queue)


async def main(page: ft.Page):
    page.title = "Apartment Listing Application"
    page.window.width = 1000
    page.window.height = 1000
    page.scroll = "auto"

    async def poll_events():
        while True:
            print("Polling events")
            event = await event_queue.get()
            print(f"Got event {event}")
            """ match event.type:
                case "auction-lost":
                    page.snack_bar = ft.SnackBar(ft.Text(event.agent))
                case "auction-completed":
                    page.snack_bar = ft.SnackBar(ft.Text("Auction completed")) """
            page.snack_bar = ft.SnackBar(ft.Text(f"Got event {event}"))
            page.snack_bar.open = True
            page.update()

    asyncio.create_task(poll_events())

    def change_tab(e):
        tabs.selected_index = e.control.selected_index
        tab_content.content = tabs_content[e.control.selected_index]
        page.update()

    # Create tabs
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text="Add Listing"),
            ft.Tab(text="View Listings"),
        ],
        on_change=change_tab,
    )
    listings = ft.Column(spacing=20, scroll=True)

    # Create the listings view
    listings_view = ft.Column([
        ft.Text("Apartment Listings", size=30, weight=ft.FontWeight.BOLD),
        ft.Divider(),
        listings,
    ], scroll="auto")


    coordinates = {
        "lat": 52.2297700,
        "lng": 21.0117800
    }

    # Initialize geocoder
    geolocator = Nominatim(user_agent="my_app")

    # Add required fields note
    required_note = ft.Text(
        "* indicates required fields",
        size=12,
        color=ft.colors.GREY_700,
        italic=True
    )

    # Error text fields
    seller_error_text = ft.Text(visible=False, color=ft.colors.RED_400, size=12)
    address_error_text = ft.Text(visible=False, color=ft.colors.RED_400, size=12)
    price_error_text = ft.Text(visible=False, color=ft.colors.RED_400, size=12)
    area_error_text = ft.Text(visible=False, color=ft.colors.RED_400, size=12)

    # Form elements
    seller_name = ft.TextField(
        label="Seller Full Name *",
        hint_text="Enter your full name",
        width=400,
        on_change=lambda _: validate_name()
    )

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

    verified_street = ft.TextField(
        label="Verified Street *",
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

    area = ft.TextField(
        label="Area (m²) *",
        hint_text="Enter apartment area",
        width=190,
        keyboard_type=ft.KeyboardType.NUMBER,
        on_change=lambda _: validate_area()
    )

    price_lower = ft.TextField(
        label="Price (USD) *",
        hint_text="Enter the price",
        width=190,
        keyboard_type=ft.KeyboardType.NUMBER,
        on_change=lambda _: validate_price()
    )

    blacklist_container = ft.Container(
        content=ft.Column([
            ft.Text("Blacklisted Premises", size=16, weight=ft.FontWeight.W_500),
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Checkbox(
                                        label=SERVICE_OPTIONS[i],
                                        value=False,
                                        on_change=lambda _: validate_form()
                                    ),
                                    width=180,
                                ),
                                ft.Container(
                                    content=ft.Checkbox(
                                        label=SERVICE_OPTIONS[i + 1],
                                        value=False,
                                        on_change=lambda _: validate_form()
                                    ) if i + 1 < len(SERVICE_OPTIONS) else ft.Container(),
                                    width=180,
                                )
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            spacing=10,
                        ) for i in range(0, len(SERVICE_OPTIONS), 2)
                    ],
                    scroll="auto",
                    height=200,
                    spacing=5,
                ),
                height=220,
            ),
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
        "Add Listing",
        on_click=lambda _: submit_form(),
        width=200,
        disabled=True
    )

    form_view = ft.Container(
        content=ft.Column([
            ft.Text("Add New Listing", size=30, weight=ft.FontWeight.BOLD),
            required_note,
            ft.Divider(),
            seller_name,
            seller_error_text,
            street,
            ft.Row([city, local_number], alignment=ft.MainAxisAlignment.START),
            location_buttons,
            verified_street,
            address_error_text,
            ft.Row([verified_apartment, verified_postal], alignment=ft.MainAxisAlignment.START),
            ft.Row([verified_voivodeship, verified_country], alignment=ft.MainAxisAlignment.START),
            ft.Row([
                ft.Column([area, area_error_text]),
                ft.Column([price_lower, price_error_text])
            ], alignment=ft.MainAxisAlignment.START),
            blacklist_container,
            description,
            submit_button,
        ], spacing=15),
        padding=20,
    )

    tabs_content = [form_view, listings_view]
    tab_content = ft.Container(
        content=tabs_content[0],
        padding=ft.padding.only(top=20)
    )


    # Validation functions
    def validate_name(_=None):
        if not seller_name.value:
            seller_error_text.value = "Seller name is required"
            seller_error_text.visible = True
            return False
        seller_error_text.visible = False
        return True

    def validate_address(_=None):
        if not verified_street.value:
            address_error_text.value = "Verified address is required"
            address_error_text.visible = True
            return False
        address_error_text.visible = False
        return True

    def validate_price(_=None):
        try:
            price = float(price_lower.value) if price_lower.value else 0
            if price <= 0:
                price_error_text.value = "Price must be greater than 0"
                price_error_text.visible = True
                return False
            price_error_text.visible = False
            return True
        except ValueError:
            price_error_text.value = "Please enter a valid price"
            price_error_text.visible = True
            return False

    def validate_area(_=None):
        try:
            area_val = float(area.value) if area.value else 0
            if area_val <= 0:
                area_error_text.value = "Area must be greater than 0"
                area_error_text.visible = True
                return False
            area_error_text.visible = False
            return True
        except ValueError:
            area_error_text.value = "Please enter a valid area"
            area_error_text.visible = True
            return False

    def validate_form():
        name_valid = validate_name()
        address_valid = validate_address()
        price_valid = validate_price()
        area_valid = validate_area()

        # Check if at least one checkbox is selected
        checkbox_valid = False
        for row in blacklist_container.content.controls[1].content.controls:
            for container in row.controls:
                if container.content and isinstance(container.content, ft.Checkbox):
                    if container.content.value:
                        checkbox_valid = True
                        break
            if checkbox_valid:
                break

        submit_button.disabled = not all([name_valid, address_valid, price_valid, area_valid, checkbox_valid])
        page.update()

    def search_location():
        try:
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

                    address_components = location_data.address.split(", ")
                    if(not address_components[0][0].isdigit() and address_components[1][0].isdigit()):
                        address_components = address_components[1:]

                    verified_street.value = ""
                    verified_apartment.value = local_number.value if local_number.value else ""
                    verified_voivodeship.value = ""
                    verified_postal.value = ""
                    verified_country.value = ""

                    if address_components[0]:
                        verified_street.value = address_components[1] + " " + address_components[0]

                    for comp in address_components:
                        if "województwo" in comp.lower():
                            verified_voivodeship.value = comp
                            break

                    for comp in address_components[1:]:
                        if any(c.isdigit() for c in comp) and len(comp) <= 10:
                            verified_postal.value = comp
                            break

                    verified_country.value = address_components[-1]

                    validate_form()
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
        # Validate all fields first
        name_valid = validate_name()
        address_valid = validate_address()
        price_valid = validate_price()
        area_valid = validate_area()

        # Check if at least one checkbox is selected
        checkbox_valid = False
        checkboxes = []
        for row in blacklist_container.content.controls[1].content.controls:
            for container in row.controls:
                if container.content and isinstance(container.content, ft.Checkbox):
                    checkboxes.append(container.content)
                    if container.content.value:
                        checkbox_valid = True

        if not all([name_valid, address_valid, price_valid, area_valid, checkbox_valid]):
            page.overlay.append(ft.SnackBar(content=ft.Text("Please correct all errors before submitting")))
            return

        address_parts = [
            verified_street.value,
            f"Apartment {verified_apartment.value}" if verified_apartment.value else "",
            verified_postal.value,
            verified_voivodeship.value,
            verified_country.value
        ]
        full_address = ", ".join([part for part in address_parts if part])

        blacklisted = [cb.label for cb in checkboxes if cb.value]

        listings.controls.append(
            ft.Card(
                content=ft.Container(content=ft.Column([
                    ft.Text(f"Seller: {seller_name.value}", size=16, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Location: {full_address}", size=16),
                    ft.Text(f"Area: {area.value} m²", size=16),
                    ft.Text(f"Price: ${price_lower.value}", size=16),
                    ft.Text(f"Description: {description.value},", size=16),
                    ft.Text(f"Blacklisted premises: {', '.join(blacklisted)}" if blacklisted else "No blacklisted premises", size=16),
                ], spacing=10), padding=20),
                width=500,
            )
        )

        details = RentalOfferDetails(
            starting_price=float(price_lower.value),
            location=[coordinates["lat"], coordinates["lng"]]
        )

        agent.add_rental_offer(details)

        # Clear form
        street.value = ""
        city.value = ""
        local_number.value = ""
        verified_street.value = ""
        verified_apartment.value = ""
        verified_voivodeship.value = ""
        verified_postal.value = ""
        verified_country.value = ""
        price_lower.value = ""
        description.value = ""
        seller_name.value = ""
        area.value = ""
        for checkbox in checkboxes:
            checkbox.value = False

        validate_form()
        page.update()

    # Main layout
    tabs.selected_index = 1
    tab_content.content = tabs_content[1]


    page.add(
        ft.Column([
            tabs,
            tab_content
        ])
    )


if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

if __name__ == "__main__":
    agent.start()
    asyncio.run(ft.app_async(target=main))