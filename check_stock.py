"""Controleert de voorraad van de PS5 Pro (2TB) bij PlayStation Direct België (playstation.com) en mailt bij een wijziging."""

import json
import os
import re
import smtplib
import sys
import urllib.error
import urllib.request
from datetime import datetime
from email.message import EmailMessage
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

# Sinds oktober 2026 zit PlayStation Direct België op playstation.com; de oude link verwijst hierheen.
PRODUCT_URL = "https://www.playstation.com/nl-be/ps5/ps5-pro/buy-now/"
PRODUCT_SKU = "PSD001-PSDE01942_39-PS5PROCHASASIRSE-E000K3A7V"
# Oude bron (direct.playstation.com), enkel gebruikt als SOURCE = "api".
OLD_PRODUCT_URL = "https://direct.playstation.com/nl-be/buy-consoles/playstation5-pro-console-2-tb"
PRODUCT_CODE = "1000050720-BX"
API_URL = (
    "https://api.direct.playstation.com/commercewebservices/ps-direct-be/users/anonymous"
    f"/products/productList?fields=BASIC&lang=nl_BE&productCodes={PRODUCT_CODE}"
)
STATE_FILE = Path(__file__).with_name("status.json")
README_FILE = Path(__file__).with_name("README.md")
BADGE_DIR = Path(__file__).with_name("badges")
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0 Safari/537.36"
)
PAGE_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "nl-BE,nl;q=0.9,en;q=0.8",
}
API_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json",
    "Origin": "https://direct.playstation.com",
    "Referer": OLD_PRODUCT_URL,
}

# Schakelaar voor de bron van de voorraadstatus:
#   "page" = productpagina op playstation.com lezen (huidige site)
#   "api"  = oude API van direct.playstation.com (geeft sinds de verhuis HTTP 403)
SOURCE = "page"
# Aantal geblokkeerde scans (HTTP 403) na elkaar voordat de run faalt en GitHub een foutmail stuurt.
MAX_BLOCKED_RUNS = 3


# Haalt de huidige voorraadstatus op via de bron die in SOURCE gekozen is.
def fetch_status() -> dict:
    return fetch_status_from_page() if SOURCE == "page" else fetch_status_from_api()


# Leest de voorraad uit de schema.org-productgegevens (JSON-LD) in de HTML van de productpagina.
def fetch_status_from_page() -> dict:
    request = urllib.request.Request(PRODUCT_URL, headers=PAGE_HEADERS)
    with urllib.request.urlopen(request, timeout=30) as response:
        html = response.read().decode("utf-8")
    for block in re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', html, re.S):
        data = json.loads(block)
        if data.get("@type") == "Product" and data.get("sku") == PRODUCT_SKU:
            offer = data["offers"]
            availability = offer["availability"].rsplit("/", 1)[-1]  # bv. "OutOfStock"
            return {
                # Zelfde notatie als de oude API ("outOfStock"), zodat status.json vergelijkbaar blijft.
                "stockLevelStatus": availability[0].lower() + availability[1:],
                "price": float(offer["price"]),
            }
    raise RuntimeError(
        f"Geen productgegevens voor SKU {PRODUCT_SKU} gevonden op {PRODUCT_URL}. "
        "Sony heeft de pagina of het product waarschijnlijk aangepast."
    )


# Haalt de voorraadstatus op via de oude API van direct.playstation.com.
def fetch_status_from_api() -> dict:
    request = urllib.request.Request(API_URL, headers=API_HEADERS)
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)
    product = next(p for p in data["products"] if p["code"] == PRODUCT_CODE)
    return {
        "stockLevelStatus": product["stock"]["stockLevelStatus"],
        "purchasable": product.get("purchasable"),
        "maxOrderQuantity": product.get("maxOrderQuantity"),
        "price": product.get("price", {}).get("value"),
    }


# Statussen (oude API en schema.org) die betekenen dat je de console niet kan kopen.
UNAVAILABLE_STATUSES = {"outOfStock", "soldOut", "discontinued"}


# Geeft True als de status betekent dat de console te koop is.
def is_available(status: str) -> bool:
    return status not in UNAVAILABLE_STATUSES


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
    available = is_available(current["stockLevelStatus"])
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
        f"[![Laatste scan](badges/lastscan.svg)]({PRODUCT_URL})\n\n"
        f"Laatste scan: **{now.strftime('%d/%m/%Y')}** om **{now.strftime('%H:%M')}**\n\n"
        "</div>\n"
    )


# Telt een door Akamai geblokkeerde scan; faalt pas als dat MAX_BLOCKED_RUNS keer na elkaar gebeurt.
def handle_blocked(previous: dict | None) -> int:
    state = dict(previous or {})
    state["blockedRuns"] = state.get("blockedRuns", 0) + 1
    STATE_FILE.write_text(json.dumps(state, indent=2) + "\n")
    blocked = state["blockedRuns"]
    if blocked >= MAX_BLOCKED_RUNS:
        print(
            f"::error::PlayStation (Akamai) blokkeert de scan al {blocked} keer na elkaar met HTTP 403. "
            "De voorraad wordt niet meer gecontroleerd tot dit opgelost is. "
            "Controleer de productpagina of zet SOURCE in check_stock.py om."
        )
        return 1
    print(f"Scan geblokkeerd door Akamai (HTTP 403), {blocked}/{MAX_BLOCKED_RUNS}. Volgende run probeert opnieuw.")
    return 0


# Vergelijkt de huidige status met de vorige, mailt bij verandering en bewaart de nieuwe status.
def main() -> int:
    previous = load_previous()
    try:
        current = fetch_status()
    except urllib.error.HTTPError as err:
        if err.code != 403:
            raise
        return handle_blocked(previous)
    print(f"Huidige status: {current}")
    print(f"Vorige status:  {previous}")

    write_readme(current)

    if "--test-mail" in sys.argv:
        send_mail("PS5 Pro monitor: testmail", f"De monitor werkt.\n\nHuidige status: {current}\n{PRODUCT_URL}")
        print("Testmail verstuurd.")
        return 0

    if previous and previous.get("stockLevelStatus") not in (None, current["stockLevelStatus"]):
        available = is_available(current["stockLevelStatus"])
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
