"""Minimal FastAPI application for the Travel Agent backend."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from travel_agent.routers import agent, health

app = FastAPI(title="Travel Agent", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health.router)
app.include_router(agent.router)
