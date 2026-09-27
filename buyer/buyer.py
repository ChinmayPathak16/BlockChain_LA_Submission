import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from dotenv import load_dotenv
import httpx

from eth_account import Account
from x402 import x402Client
from x402.mechanisms.evm import EthAccountSigner
from x402.mechanisms.evm.exact import ExactEvmClientScheme
from x402.http.clients.httpx import wrapHttpxWithPayment

load_dotenv()

SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000").rstrip("/")
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")

def get_x402_client() -> x402Client:
    key = PRIVATE_KEY.strip()
    if not key:
        print(
            "Error: PRIVATE_KEY environment variable is not set.\n"
            "Set it in your .env file (see .env.example).\n"
            "Never hard-code private keys in source files.",
            file=sys.stderr,
        )
        sys.exit(1)
    if not key.startswith("0x"):
        key = "0x" + key

    account = Account.from_key(key)
    signer = EthAccountSigner(account)

    client = x402Client()
    client.register("eip155:84532", ExactEvmClientScheme(signer))
    client.register("base-sepolia", ExactEvmClientScheme(signer))
    return client

async def run_preview(notice_text: str):
    url = f"{SERVER_URL}/parse/preview"
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json={"notice": notice_text})
    
    print(f"HTTP Status: {resp.status_code}")
    try:
        print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
    except Exception:
        print(resp.text)
    
    if resp.status_code != 200:
        sys.exit(1)

async def run_single(notice_text: str):
    x402_cl = get_x402_client()
    url = f"{SERVER_URL}/parse"

    async with wrapHttpxWithPayment(x402_cl) as client:
        resp = await client.post(url, json={"notice": notice_text})

    print(f"HTTP Status: {resp.status_code}")
    try:
        body = resp.json()
        print(json.dumps(body, indent=2, ensure_ascii=False))
    except Exception:
        print(resp.text)

    if resp.status_code == 422:
        print("\n[RESULT] 422 Unprocessable Entity - Parsing failed. NO payment was settled.", file=sys.stderr)
        sys.exit(1)
    elif resp.status_code != 200:
        sys.exit(1)
    else:
        print("\n[RESULT] 200 OK - Parsing succeeded. Payment was successfully settled.")

async def run_bulk(notices: list[str]):
    x402_cl = get_x402_client()
    url = f"{SERVER_URL}/parse/bulk"

    async with wrapHttpxWithPayment(x402_cl) as client:
        resp = await client.post(url, json={"notices": notices})

    print(f"HTTP Status: {resp.status_code}")
    try:
        body = resp.json()
        print(json.dumps(body, indent=2, ensure_ascii=False))
    except Exception:
        print(resp.text)

    if resp.status_code == 422:
        print("\n[RESULT] 422 Unprocessable Entity - All notices failed. NO payment was settled.", file=sys.stderr)
        sys.exit(1)
    elif resp.status_code != 200:
        sys.exit(1)
    else:
        print("\n[RESULT] 200 OK - Bulk parse completed. Payment settled.")

def main():
    parser = argparse.ArgumentParser(description="Meera's Railway Delay Notice x402 Buyer CLI")
    parser.add_argument("--route", choices=["single", "bulk", "preview"], required=True, help="API route to target")
    parser.add_argument("--file", type=str, help="Path to input notice text file")
    parser.add_argument("--dir", type=str, help="Directory containing notice text files for bulk route")
    parser.add_argument("--text", type=str, help="Raw notice text string")

    args = parser.parse_args()

    if args.route == "preview":
        if args.file:
            notice_text = Path(args.file).read_text(encoding="utf-8")
        elif args.text:
            notice_text = args.text
        else:
            print("Error: --file or --text is required for preview route", file=sys.stderr)
            sys.exit(1)
        asyncio.run(run_preview(notice_text))

    elif args.route == "single":
        if args.file:
            notice_text = Path(args.file).read_text(encoding="utf-8")
        elif args.text:
            notice_text = args.text
        else:
            print("Error: --file or --text is required for single route", file=sys.stderr)
            sys.exit(1)
        asyncio.run(run_single(notice_text))

    elif args.route == "bulk":
        notices = []
        if args.dir:
            dir_path = Path(args.dir)
            if not dir_path.is_dir():
                print(f"Error: Directory {args.dir} does not exist", file=sys.stderr)
                sys.exit(1)
            for f in sorted(dir_path.glob("*.txt")):
                content = f.read_text(encoding="utf-8").strip()
                if content:
                    notices.append(content)
            notices = notices[:20]  # Cap at 20 max
        elif args.file:
            notices.append(Path(args.file).read_text(encoding="utf-8"))
        elif args.text:
            notices.append(args.text)
        else:
            print("Error: --dir or --file or --text is required for bulk route", file=sys.stderr)
            sys.exit(1)
        asyncio.run(run_bulk(notices))

if __name__ == "__main__":
    main()
