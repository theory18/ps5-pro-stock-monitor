# PS5 Pro voorraadmonitor

- [x] robots.txt controleren (alleen /account-settings en /checkout verboden)
- [x] Pagina ophalen en tekst "Momenteel niet beschikbaar" zoeken (staat er altijd als label, dus onbruikbaar)
- [x] Echte bron vinden: productList-API -> stock.stockLevelStatus
- [x] check_stock.py (alleen stdlib, mailt bij statuswijziging)
- [x] GitHub Actions workflow (elke 5 min, status.json wordt gecommit)
- [x] Lokaal getest, inclusief gesimuleerde statuswijziging
- [ ] Repo aanmaken + secrets instellen + testmail versturen

## Review
Checken op de HTML-tekst zou altijd "niet beschikbaar" vinden, omdat het label in de pagina-config staat.
De API geeft de echte status terug en is betrouwbaarder. Nog niet getest: of Akamai GitHub-IP's blokkeert.
