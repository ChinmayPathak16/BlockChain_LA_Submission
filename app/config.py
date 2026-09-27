import os
from dotenv import load_dotenv

load_dotenv()

# Network configuration
# x402 network string: "base-sepolia" or "eip155:84532"
NETWORK = os.getenv("NETWORK", "base-sepolia")

# Facilitator URL
FACILITATOR_URL = os.getenv("FACILITATOR_URL", "https://x402.org/facilitator")

# Seller payment wallet address
PAY_TO_ADDRESS = os.getenv("PAY_TO_ADDRESS", "0x0000000000000000000000000000000000000000")

# Prices in USD / USDC
PRICE_SINGLE = "0.001"
PRICE_BULK = "0.008"

# Server configuration
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000")

# Buyer private key (used by buyer CLI script)
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")
