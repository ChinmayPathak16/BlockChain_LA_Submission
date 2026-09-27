# Meera's Railway Delay Notice x402 API

A FastAPI micro-service that parses messy Indian Railways delay notices (English / Hindi / Marathi) into structured JSON and charges **per call** using [x402](https://x402.org) micropayments on **Base Sepolia** testnet USDC.

---

## Project layout

```
.
├── app/
│   ├── config.py          # env-driven settings
│   ├── main.py            # FastAPI app + x402 middleware
│   ├── models.py          # Pydantic v2 schemas
│   ├── parser.py          # notice parser (raises ParseError on failure)
│   └── routes/
│       ├── free.py        # GET /health, POST /parse/preview  (free)
│       ├── single.py      # POST /parse                       ($0.001)
│       └── bulk.py        # POST /parse/bulk                  ($0.008, ≤20)
├── buyer/
│   └── buyer.py           # Python CLI that auto-pays via x402
├── samples/
│   ├── good_01.txt … good_05.txt   # parseable notices
│   └── bad_01.txt  … bad_05.txt    # notices that trigger ParseError
├── tests/
│   └── test_parser.py     # 10 pytest cases (5 pass / 5 fail)
├── .env.example
└── requirements.txt
```

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.10+ |
| A Base Sepolia wallet | funded with test USDC |

Get free Base Sepolia testnet USDC from [https://faucet.circle.com](https://faucet.circle.com) (select Base Sepolia).

---

## Quick start

### 1 — Clone & create virtual environment

```bash
git clone <this-repo>
cd meera-railway-delay-api
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2 — Configure `.env`

```bash
cp .env.example .env
```

Edit `.env`:

```env
PAY_TO_ADDRESS=0xYOUR_SELLER_WALLET_ADDRESS   # receives payments
PRIVATE_KEY=0xYOUR_BUYER_PRIVATE_KEY          # wallet that pays (testnet only)
```

Leave `FACILITATOR_URL`, `NETWORK`, and `SERVER_URL` at their defaults for local testing.

### 3 — Run the server

```bash
uvicorn app.main:app --reload
```

Server starts at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

### 4 — Run the test suite

```bash
pytest tests/ -v
```

All 10 tests should pass in < 1 s.

---

## API reference

### `GET /health` — free, no payment

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

---

### `POST /parse/preview` — free, truncated output

Returns a **masked** preview so callers can decide whether to pay.

```bash
curl -X POST http://localhost:8000/parse/preview \
  -H "Content-Type: application/json" \
  -d '{"notice": "Train 12951 arriving at NDLS expected 14:30 due to signal failure"}'
```

```json
{"train_number":"12***","station_code":"N***","expected_time":"14:**","reason":null}
```

---

### `POST /parse` — **$0.001 USDC** (paid, Base Sepolia)

Returns full structured JSON.  
**Never charged if the notice cannot be parsed** (server returns HTTP 422 before x402 settles).

```json
{
  "train_number": "12951",
  "station_code": "NDLS",
  "expected_time": "14:30",
  "reason": "signal failure"
}
```

#### Using the buyer CLI

```bash
# from a single file
python buyer/buyer.py --route single --file samples/good_01.txt

# inline text
python buyer/buyer.py --route single --text "Train 12951 NDLS 14:30 due to fog"

# expect 422 — no payment charged
python buyer/buyer.py --route single --file samples/bad_01.txt
```

---

### `POST /parse/bulk` — **$0.008 USDC** (paid, Base Sepolia, max 20 notices)

Accepts a list of notices; returns per-notice results with any parse errors inlined.  
**If every single notice fails, returns HTTP 422 — no payment charged.**

```json
{
  "notices": [
    "Train 12951 NDLS 14:30 due to fog",
    "ट्रेन 12137 CSMT 09:15 कारण तकनीकी खराबी"
  ]
}
```

#### Using the buyer CLI

```bash
# send a whole directory of .txt files (up to 20)
python buyer/buyer.py --route bulk --dir samples/

# single file as a one-element bulk
python buyer/buyer.py --route bulk --file samples/good_02.txt
```

---

## x402 payment flow (how it works)

1. Buyer sends `POST /parse` **without** a payment header.  
2. Server replies `402 Payment Required` with a JSON body describing the price, network, and payment address.  
3. The `wrapHttpxWithPayment` wrapper in the buyer CLI signs a Base Sepolia USDC transfer and retries the request with an `X-PAYMENT` header.  
4. The x402 facilitator at `https://x402.org/facilitator` verifies and settles the transaction.  
5. Server processes the notice and returns the result.  
6. **If the parser raises `ParseError` the endpoint returns HTTP 422 before settlement completes — the buyer is never charged.**

---

## Parser rules

| Field | Required | Extraction rule |
|-------|----------|-----------------|
| `train_number` | ✅ | First standalone 4–5 digit run (`\b\d{4,5}\b`) |
| `station_code` | ✅ | First `\b[A-Z]{2,5}\b` not in noise-word list (PNR, SMS, HTTP …) |
| `expected_time` | ✅ | `HH:MM` or `HH.MM` in 24-h range, normalised to `HH:MM` |
| `reason` | ❌ | Text after `due to` / `reason:` / `कारण` / `मुळे` |

`ParseError` is raised (and HTTP 422 returned) if any required field is absent.

---

## Design decisions (noted per spec)

- **`eip155:84532`** is registered as the canonical network string; `"base-sepolia"` is registered as an alias so either form in env works.
- Prices are set as plain strings (`"0.001"`, `"0.008"`) — the x402 `PaymentOption` schema expects string USD amounts.
- The buyer CLI falls back to the Hardhat/Anvil well-known test key `0xac0974...` when `PRIVATE_KEY` is not set, allowing smoke-testing without a real wallet.
- Bulk route charges only when ≥ 1 notice succeeds; partial success is billed, errors are inlined in the response.
