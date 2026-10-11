<div align="center">

# 🎮 PS5 Pro voorraadmonitor

Houdt de **PlayStation®5 Pro Console – 2TB** op [PlayStation Direct België](https://direct.playstation.com/nl-be/buy-consoles/playstation5-pro-console-2-tb) in de gaten<br>
en stuurt een e-mail zodra de beschikbaarheid verandert.

<br>

[![Voorraad](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2Ftheory18%2Fps5-pro-stock-monitor%2Fstatus%2Fstock.json&style=for-the-badge)](https://direct.playstation.com/nl-be/buy-consoles/playstation5-pro-console-2-tb)

[![Laatste scan](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2Ftheory18%2Fps5-pro-stock-monitor%2Fstatus%2Flastscan.json&style=for-the-badge)](https://github.com/theory18/ps5-pro-stock-monitor/actions/workflows/check-stock.yml)
[![Workflow](https://img.shields.io/github/actions/workflow/status/theory18/ps5-pro-stock-monitor/check-stock.yml?branch=main&style=for-the-badge&label=scraper)](https://github.com/theory18/ps5-pro-stock-monitor/actions/workflows/check-stock.yml)

</div>

---

## 📡 Status lezen

| Badge | Betekenis |
|---|---|
| **PS5 Pro 2TB** | 🟥 `niet beschikbaar` of 🟩 `BESCHIKBAAR`, zoals bij de laatste scan |
| **laatste scan** | Datum en uur (Belgische tijd) van de laatste geslaagde check |
| **scraper** | `passing` als de laatste run gelukt is, `failing` als er iets misging |

> **Loopt de scraper nog?** De laatste scan hoort hooguit ±20 minuten oud te zijn.
> Is hij veel ouder, kijk dan bij [Actions](https://github.com/theory18/ps5-pro-stock-monitor/actions/workflows/check-stock.yml).
> GitHub schakelt geplande runs uit na 60 dagen zonder activiteit; daar kun je ze met één klik weer aanzetten.

## ⚙️ Hoe het werkt

1. Elke 5 minuten start GitHub Actions `check_stock.py`.
2. Het script vraagt de voorraad op bij dezelfde API die de website gebruikt (`stockLevelStatus`).
3. Is de status anders dan in `status.json`, dan volgt er een mail en wordt de nieuwe status opgeslagen.
4. De badges hierboven komen uit de `status`-branch, die bij elke run wordt overschreven.

## 🔑 Secrets

| Secret | Inhoud |
|---|---|
| `SMTP_USER` | Gmail-adres dat de mail verstuurt |
| `SMTP_PASSWORD` | Gmail-app-wachtwoord |
| `MAIL_TO` | *(optioneel)* ontvanger, standaard `SMTP_USER` |

**Testmail:** Actions → *PS5 Pro voorraadcheck* → *Run workflow* → vink *Stuur een testmail* aan.
