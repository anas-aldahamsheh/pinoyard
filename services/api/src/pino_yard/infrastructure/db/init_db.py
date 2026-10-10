"""Prepare a database from the command line: migrations, initial data, administrator checks.

    python -m pino_yard.infrastructure.db.init_db

The server does the same at start-up; this is for setting up a database ahead of time.
"""
import asyncio

from pino_yard.infrastructure.db.migrations.runner import migrate_database
from pino_yard.infrastructure.db.seed import seed_database
from pino_yard.infrastructure.db.session import async_session_factory, engine


async def init_and_seed() -> None:
    print("Applying database migrations...")
    state = await migrate_database(engine)
    print(f"Schema up to date (database was: {state}).")

    async with async_session_factory() as session:
        print("Adding initial Pino Yard data where missing...")
        await seed_database(session)

    from pino_yard.application.account_security import secure_accounts_on_startup
    async with async_session_factory() as session:
        await secure_accounts_on_startup(session)
    await engine.dispose()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(init_and_seed())
