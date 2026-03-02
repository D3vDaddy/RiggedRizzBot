# utils.py
from aiogram import html

def get_display_name(first_name, last_name):
    full_name = first_name
    if last_name:
        full_name += f" {last_name}"
    return escape_html(full_name)

def escape_html(text: str) -> str:
    if not text: return ""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
