# Checkout Bot Card Collection

An automated bot for monitoring and purchasing collectible cards from e-commerce sites, with a specific focus on ToysCenter.it.

## Overview

The bot:

- Polls a product page until stock is available
- Solves Cloudflare Turnstile via CapSolver
- Adds the product to the cart and proceeds to checkout
- Fills the address form and submits the Adyen credit-card payment
- Runs many tasks concurrently from a single CSV file

The implementation uses **async [patchright](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright)** (a stealth-patched Playwright fork) instead of Selenium, with proper page objects, structured logging, and validated configuration.

## Demo

https://github.com/user-attachments/assets/2b6ac76a-0689-4499-82f7-e26bcb2b0e95

## Requirements

- Python 3.10+
- A CapSolver account (`https://capsolver.com`)
- A Chromium build (`patchright install chromium`)

## Project structure

```
checkout_bot/
├── __main__.py              # python -m checkout_bot
├── config/
│   ├── settings.py          # AppSettings (loads .env)
│   └── task.py              # TaskRow + load_tasks() for the CSV
├── core/
│   ├── orchestrator.py      # async runner with retry + concurrency
│   ├── browser.py           # patchright launch helper
│   ├── sleep_prevention.py  # macOS caffeinate / Windows wake helper
│   └── exceptions.py        # CheckoutError hierarchy
├── pages/
│   ├── base_page.py         # cookies + captcha helpers
│   ├── product_page.py      # availability poll + add to cart
│   ├── cart_page.py         # proceed to checkout
│   ├── checkout_form_page.py# billing form fill
│   ├── shipping_step_page.py# shipping method selection
│   └── payment_page.py      # Adyen iframes + confirmation
├── services/
│   ├── captcha_solver.py    # async CapSolver client
│   └── province_lookup.py   # Italian province → code
└── utils/
    ├── logging.py           # logger + task-id context
    └── random_data.py       # random_string / random_phone

tasks/toyscenter.csv         # one row per concurrent checkout attempt
.env                         # TOYS_CENTER_KEY + CAPSOLVER_API_KEY
.env.example                 # template — copy to .env and fill in
```

## Setup

```bash
git clone https://github.com/<your-user>/Checkout-bot-Card-Collection.git
cd Checkout-bot-Card-Collection

pip install -r requirements.txt
patchright install chromium
```

Copy `.env.example` to `.env` and fill in real values:

```bash
cp .env.example .env
```

```
TOYS_CENTER_KEY=0x4AAAAAAA_slGZ9sK4UREXX
CAPSOLVER_API_KEY=your-capsolver-api-key
```

Fill `tasks/toyscenter.csv` with one row per checkout attempt. Required columns: `product_link`, `email`, `surname`, `address_line_1`, `city`, `state`, `zipcode`, `titolare_carta`, `numero_carta`, `scadenza_carta` (MM/YY), `cvv`.

## Run

```bash
python -m checkout_bot
```

Each CSV row spawns a concurrent task (bounded by `max_concurrency`, default 10). Tasks retry automatically every `restart_delay_seconds` on failure until they succeed or you interrupt with Ctrl-C.

## Configuration knobs

`AppSettings` (`checkout_bot/config/settings.py`) exposes:

| Field | Default | Purpose |
|---|---|---|
| `max_concurrency` | 10 | Concurrent in-flight checkouts |
| `refresh_interval_seconds` | 2.0 | Product availability poll cadence |
| `restart_delay_seconds` | 10.0 | Delay before retrying a failed attempt |
| `headless` | False | Run Chromium headless |
| `log_level` | INFO | Standard logging level |
| `payment_confirmation_timeout_seconds` | 60 | How long to wait for "Grazie per il tuo ordine" |
| `captcha_poll_max_attempts` | 60 | Max polls before giving up on CapSolver |
| `captcha_poll_interval_seconds` | 2.0 | CapSolver poll cadence |

## Troubleshooting

### `BrowserType.launch: Executable doesn't exist at …/ms-playwright/chromium-XXXX/…`

patchright can't find the Chromium binary. This happens on a fresh checkout, after a patchright upgrade, or inside a new virtualenv. Install the browser into the active environment:

```bash
patchright install chromium
```

If you're using a virtualenv, make sure you run the command with that venv active (or invoke it explicitly, e.g. `.venv/bin/patchright install chromium`). Then re-run `python -m checkout_bot`.

## Security note

Credit-card data and emails live in `tasks/toyscenter.csv` in plain text. Treat the file as a secret — do not commit it.

## Legal

For educational purposes only. Automated purchasing may violate site terms of service. The author assumes no responsibility for any consequences of using this software.
