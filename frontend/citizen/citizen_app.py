import flet as ft
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'database')))

from system_data import SERVICE_OPTIONS

def main(page: ft.Page):
    page.title = "Formularz zgłoszenia zapotrzebowania"
    page.vertical_alignment = ft.MainAxisAlignment.START

    name_input = ft.TextField(label="Imię i nazwisko", autofocus=True)
    service_input = ft.Dropdown(
        label="Usługa",
        options=[ft.dropdown.Option(name) for name in SERVICE_OPTIONS],
    )
    description_input = ft.TextField(label="Opis zapotrzebowania", multiline=True, min_lines=3, max_lines=5)

    def submit_form(e):
        name = name_input.value
        service = service_input.value
        description = description_input.value
        
        print(f"Nowe zapotrzebowanie:\nImię: {name}\nUsługa: {service}\nOpis: {description}")
        text = ft.Text(f"Dziękujemy za zgłoszenie zapotrzebowania!")
        text.padding = ft.padding.all(20)
        page.add(text)

    submit_button = ft.ElevatedButton("Wyślij zapotrzebowanie", on_click=submit_form)

    page.add(name_input, service_input, description_input, submit_button)

ft.app(target=main)
