import flet as ft

def main(page: ft.Page):
    page.title = "Rent or Lend a Location"

    def show_initial_screen():
        page.controls.clear()
        first_screen = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text("Rent", size=30, color=ft.colors.WHITE, text_align="center"),
                    bgcolor=ft.colors.BLUE,
                    expand=True,
                    alignment=ft.alignment.center,
                    on_click=lambda e: navigate_to_form("rent"),
                    height=400
                ),
                ft.Container(
                    content=ft.Text("Lend", size=30, color=ft.colors.WHITE, text_align="center"),
                    bgcolor=ft.colors.GREEN,
                    expand=True,
                    alignment=ft.alignment.center,
                    on_click=lambda e: navigate_to_form("lend"),
                    height=400
                )
            ],
            expand=True
        )
        page.add(first_screen)
        page.update()

    def navigate_to_form(option: str):
        page.controls.clear()

        if option == "rent":
            form_title = "Enter the location details to Rent a place"
        else:
            form_title = "Enter the location details to Lend a place"

        form_content = ft.Column(
            controls=[
                ft.Text(form_title),
                ft.TextField(label="Location Name"),
                ft.TextField(label="Area (sq ft)"),
                ft.TextField(label="Price per month"),
                ft.ElevatedButton("Submit", on_click=lambda e: submit_form(option)),
                ft.ElevatedButton("Back", on_click=lambda e: show_initial_screen())  # Back button
            ]
        )
        
        page.add(form_content)
        page.update()

    def submit_form(option: str):
        if option == "rent":
            print("Submitting Rent form!")
        elif option == "lend":
            print("Submitting Lend form!")

    show_initial_screen()

ft.app(target=main)
