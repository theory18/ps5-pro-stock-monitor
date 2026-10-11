"""Controleert de voorraad van de PS5 Pro (2TB) op PlayStation Direct België en mailt bij een wijziging."""

import json
import os
import smtplib
import sys
import urllib.request
from datetime import datetime
from email.message import EmailMessage
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

PRODUCT_CODE = "1000050720-BX"
PRODUCT_URL = "https://direct.playstation.com/nl-be/buy-consoles/playstation5-pro-console-2-tb"
API_URL = (
    "https://api.direct.playstation.com/commercewebservices/ps-direct-be/users/anonymous"
    f"/products/productList?fields=BASIC&lang=nl_BE&productCodes={PRODUCT_CODE}"
)
STATE_FILE = Path(__file__).with_name("status.json")
README_FILE = Path(__file__).with_name("README.md")
BADGE_DIR = Path(__file__).with_name("badges")
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/140.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Origin": "https://direct.playstation.com",
    "Referer": PRODUCT_URL,
}


# Haalt de huidige voorraadstatus van het product op via de API die de website zelf gebruikt.
def fetch_status() -> dict:
    request = urllib.request.Request(API_URL, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)
    product = next(p for p in data["products"] if p["code"] == PRODUCT_CODE)
    return {
        "stockLevelStatus": product["stock"]["stockLevelStatus"],
        "purchasable": product.get("purchasable"),
        "maxOrderQuantity": product.get("maxOrderQuantity"),
        "price": product.get("price", {}).get("value"),
    }


# Leest de laatst opgeslagen status, of None als er nog geen is.
def load_previous() -> dict | None:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return None


# Stuurt een e-mail via SMTP met de gegevens uit de omgevingsvariabelen.
def send_mail(subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = os.environ["SMTP_USER"]
    msg["To"] = os.environ.get("MAIL_TO") or os.environ["SMTP_USER"]
    msg.set_content(body)
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "465"))
    with smtplib.SMTP_SSL(host, port, timeout=30) as smtp:
        smtp.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        smtp.send_message(msg)


# Maakt een SVG-badge in de stijl van shields.io "for-the-badge", zodat GitHub hem zonder externe dienst toont.
def make_badge(label: str, message: str, color: str) -> str:
    label, message = label.upper(), message.upper()
    width = lambda text: round(len(text) * 7.6) + 20
    lw, mw = width(label), width(message)
    text = lambda x, w, t: (
        f'<text x="{x + w / 2}" y="18" text-anchor="middle" textLength="{w - 20}" '
        f'lengthAdjust="spacingAndGlyphs">{escape(t)}</text>'
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{lw + mw}" height="28" role="img" '
        f'aria-label="{escape(label)}: {escape(message)}">'
        f'<rect width="{lw}" height="28" fill="#555"/>'
        f'<rect x="{lw}" width="{mw}" height="28" fill="{color}"/>'
        '<g fill="#fff" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="10" font-weight="bold">'
        f"{text(0, lw, label)}{text(lw, mw, message)}</g></svg>\n"
    )


# Schrijft de badges en de README met voorraad en laatste scan, met daaronder datum en uur als tekst.
def write_readme(current: dict) -> None:
    now = datetime.now(ZoneInfo("Europe/Brussels"))
    available = current["stockLevelStatus"] != "outOfStock"
    BADGE_DIR.mkdir(exist_ok=True)
    (BADGE_DIR / "stock.svg").write_text(make_badge(
        "PS5 Pro 2TB",
        "Beschikbaar" if available else "niet beschikbaar",
        "#4c1" if available else "#e05d44",
    ))
    (BADGE_DIR / "lastscan.svg").write_text(make_badge("laatste scan", now.strftime("%d/%m/%Y %H:%M"), "#007ec6"))
    README_FILE.write_text(
        '<div align="center">\n\n'
        "# 🎮 PS5 Pro 2TB\n\n"
        f"[![Voorraad](badges/stock.svg)]({PRODUCT_URL})\n\n"
        "![Laatste scan](badges/lastscan.svg)\n\n"
        f"Laatste scan: **{now.strftime('%d/%m/%Y')}** om **{now.strftime('%H:%M')}**\n\n"
        "</div>\n"
    )


# Vergelijkt de huidige status met de vorige, mailt bij verandering en bewaart de nieuwe status.
def main() -> int:
    current = fetch_status()
    previous = load_previous()
    print(f"Huidige status: {current}")
    print(f"Vorige status:  {previous}")

    write_readme(current)

    if "--test-mail" in sys.argv:
        send_mail("PS5 Pro monitor: testmail", f"De monitor werkt.\n\nHuidige status: {current}\n{PRODUCT_URL}")
        print("Testmail verstuurd.")
        return 0

    if previous is not None and previous["stockLevelStatus"] != current["stockLevelStatus"]:
        available = current["stockLevelStatus"] != "outOfStock"
        subject = (
            "PS5 Pro is BESCHIKBAAR op PlayStation Direct!"
            if available
            else "PS5 Pro is weer niet beschikbaar"
        )
        body = (
            f"Status veranderd: {previous['stockLevelStatus']} -> {current['stockLevelStatus']}\n"
            f"Prijs: €{current['price']}\n\n{PRODUCT_URL}\n"
        )
        send_mail(subject, body)
        print(f"Mail verstuurd: {subject}")

    if previous != current:
        STATE_FILE.write_text(json.dumps(current, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
