import flet as ft
from geopy.geocoders import Nominatim
import sys
import os
import asyncio
import uuid

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'database')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from system_data import SERVICE_OPTIONS
from agents.future_tenant.main import FutureTenantInterface, TenantOfferDetails


event_queue = asyncio.Queue()
agents = FutureTenantInterface(event_queue)


async def main(page: ft.Page):
    page.title = "Rental Offer Application"
    page.window.width = 1000
    page.window.height = 1000
    page.scroll = "auto"

    state = {
        "offers": [],
        "current_offer_idx": 0,
    }

    async def poll_events():
        while True:
            print("Polling events")

            event = await event_queue.get()
            print(f"Got event {event}")
            match event["type"]:
                case "auction-start":
                    page.snack_bar = ft.SnackBar(content=ft.Text("Auction started!"))
                    agent_id = event["agent"].localpart
                    offer_id = event["data"]["offer_id"]

                    for idx, offer in enumerate(state["offers"]):
                        if offer["agent_id"] == agent_id:
                            state["offers"][idx]["offer_id"] = offer_id
                            break

                    place_bid(idx)

                case "outbid-notification":
                    current_highest_bid = event["data"]["current_highest_bid"]
                    page.snack_bar = ft.SnackBar(content=ft.Text("You have been outbid with {current_highest_bid}!"))
                case "auction-stop":
                    page.snack_bar = ft.SnackBar(content=ft.Text("Auction ended!"))
                case "confirmation-request":
                    offer_id = event["data"]["offer_id"]
                    bid_amount = event["data"]["bid_amount"]

                    open_confirmation_modal(event["agent"].localpart, offer_id, bid_amount)
                case "auction-lost":
                    page.snack_bar = ft.SnackBar(content=ft.Text("You have lost the auction!"))

    asyncio.create_task(poll_events())

    def open_confirmation_modal(agent_id, offer_id, bid_amount):
        def confirm_offer(e):
            agents.add_confirm_bhv(agent_id, offer_id, True)
            page.show_snack_bar(ft.SnackBar(content=ft.Text(f"Offer {agent_id} confirmed with bid {bid_amount}!")))
            page.update()
            dialog.open = False
            page.update()

        def cancel_offer(e):
            agents.add_confirm_bhv(agent_id, offer_id, False)
            dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Offer"),
            content=ft.Text(f"Do you want to accept this offer with bid amount {bid_amount}?"),
            actions=[
                ft.TextButton("Confirm", on_click=confirm_offer),
                ft.TextButton("Cancel", on_click=cancel_offer),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.dialog = dialog
        dialog.open = True
        page.update()


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
        value="John Doe"
    )

    street = ft.TextField(
        label="Street Address or Location Name *",
        hint_text="Enter street name and number",
        width=400,
        on_change=lambda _: validate_form(),
        value="Zlota 22"
    )

    city = ft.TextField(
        label="City (optional)",
        hint_text="Enter city",
        width=190,
        on_change=lambda _: validate_form(),
        value="Warszawa"
    )

    verified_address = ft.TextField(
        label="Verified Address",
        width=400,
        read_only=True,
    )

    min_price = ft.TextField(
        label="Minimum Price (USD) *",
        hint_text="Enter the minimum price",
        width=190,
        keyboard_type=ft.KeyboardType.NUMBER,
        on_change=lambda _: validate_form(),
        value="1"
    )

    max_price = ft.TextField(
        label="Maximum Price (USD) *",
        hint_text="Enter the maximum price",
        width=190,
        keyboard_type=ft.KeyboardType.NUMBER,
        on_change=lambda _: validate_form(),
        value="1000000000"
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
        width=400,
        value="Spacious apartment in the city center"
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

    def place_bid(idx):
        try:
            agent_id = state["offers"][idx]["agent_id"]
            offer_id = state["offers"][idx]["offer_id"]
        except IndexError:
            page.show_snack_bar(ft.SnackBar(content=ft.Text("Auction not started yet")))
            return

        bid_amount_input = ft.TextField(label="Bid Amount", autofocus=True)

        def submit_bid(e):
            bid_amount = bid_amount_input.value
            agents.add_bid_bhv(agent_id, offer_id, int(bid_amount))

            page.show_snack_bar(ft.SnackBar(content=ft.Text(f"Placing bid of {bid_amount}...")))
            page.update()
            dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Place Bid"),
            content=ft.Column([
                bid_amount_input,
            ]),
            actions=[
                ft.TextButton("Submit", on_click=submit_bid),
                ft.TextButton("Cancel", on_click=lambda e: setattr(dialog, 'open', False)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.dialog = dialog
        dialog.open = True
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
                    ft.Divider(),
                    # ft.Text("Auction Status", size=16, weight=ft.FontWeight.BOLD),
                    # ft.Text("Status: Waiting", size=16, color=ft.colors.GREY_700),
                    # ft.Text("Current Highest Bid: N/A", size=16),
                    # ft.Text("Your Current Bid: N/A", size=16),
                    ft.ElevatedButton(
                        "Place Bid",
                        on_click=lambda _: place_bid(state["current_offer_idx"]),
                        color=ft.colors.WHITE,
                        bgcolor=ft.colors.BLUE_400,
                        width=200
                    ),
                ], spacing=10), padding=20),
                width=500,
            )
        )
        state["current_offer_idx"] += 1

        details = TenantOfferDetails(
            min_price=float(min_price.value),
            max_price=float(max_price.value),
            location=(coordinates["lat"], coordinates["lng"]),
        )
        agent_id = f"tenant_{uuid.uuid4().hex[:8]}"
        state["offers"].append({"agent_id": agent_id, "offer_id": None})

        agents.register_tenant(agent_id, details)

        # Clear form fields...
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

if __name__ == "__main__":
    asyncio.run(ft.app_async(target=main))