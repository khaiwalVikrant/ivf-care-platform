"""Seed data for the task_manager database."""

from __future__ import annotations

from task_manager.db.database import Database

PRICE_BENCHMARKS = [
    {"item_name": "Gonal-F 450IU", "item_type": "medication", "benchmark_price": 6200.0},
    {"item_name": "Menopur 75IU", "item_type": "medication", "benchmark_price": 1800.0},
    {"item_name": "Cetrotide 0.25mg", "item_type": "medication", "benchmark_price": 3500.0},
    {"item_name": "Progesterone 400mg", "item_type": "medication", "benchmark_price": 450.0},
    {"item_name": "AMH blood test", "item_type": "test", "benchmark_price": 1200.0},
    {"item_name": "FSH blood test", "item_type": "test", "benchmark_price": 800.0},
    {"item_name": "Antral follicle count ultrasound", "item_type": "test", "benchmark_price": 1500.0},
    {"item_name": "Semen analysis", "item_type": "test", "benchmark_price": 1000.0},
]


async def seed_price_benchmarks(db: Database) -> None:
    """Seed common IVF price benchmarks if they don't already exist."""
    for entry in PRICE_BENCHMARKS:
        existing = await db.get_price_benchmark(entry["item_name"])
        if existing is None:
            await db.create_price_benchmark(
                item_name=entry["item_name"],
                item_type=entry["item_type"],
                benchmark_price=entry["benchmark_price"],
            )
