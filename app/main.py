from fastapi import FastAPI
from x402 import x402ResourceServer
from x402.mechanisms.evm.exact import ExactEvmServerScheme
from x402.http import HTTPFacilitatorClient
from x402.http.types import PaymentOption, RouteConfig
from x402.http.middleware.fastapi import payment_middleware

from app.config import (
    FACILITATOR_URL,
    PAY_TO_ADDRESS,
    NETWORK,
    PRICE_SINGLE,
    PRICE_BULK,
)
from app.routes.free import router as free_router
from app.routes.single import router as single_router
from app.routes.bulk import router as bulk_router

app = FastAPI(
    title="Meera's Railway Delay Notice x402 API",
    description="Parser for messy Indian Railways delay notices with x402 micropayments on Base Sepolia",
    version="1.0.0",
)

target_network = "eip155:84532" if NETWORK in ("base-sepolia", "eip155:84532") else NETWORK

# Initialize Facilitator client and x402 resource server
facilitator = HTTPFacilitatorClient({"url": FACILITATOR_URL})
server = x402ResourceServer(facilitator)

# Register EVM exact schemes for both network string formats
server.register("eip155:84532", ExactEvmServerScheme())
server.register("base-sepolia", ExactEvmServerScheme())

# Explicit RouteConfig & PaymentOption objects to ensure price parsing ($0.001 and $0.008) is exact
routes = {
    "POST /parse": RouteConfig(
        accepts=PaymentOption(
            scheme="exact",
            pay_to=PAY_TO_ADDRESS,
            price=PRICE_SINGLE,
            network=target_network,
        )
    ),
    "POST /parse/bulk": RouteConfig(
        accepts=PaymentOption(
            scheme="exact",
            pay_to=PAY_TO_ADDRESS,
            price=PRICE_BULK,
            network=target_network,
        )
    ),
}

# Attach payment middleware to FastAPI with sync_facilitator_on_start=True (fetches facilitator /supported on start)
mw = payment_middleware(routes=routes, server=server, sync_facilitator_on_start=True)

@app.middleware("http")
async def x402_middleware(request, call_next):
    return await mw(request, call_next)

app.include_router(free_router)
app.include_router(single_router)
app.include_router(bulk_router)
