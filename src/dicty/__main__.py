import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

from loguru import logger
from alembic import command
from alembic.config import Config
from grpc import aio as grpc
from sqlalchemy.ext.asyncio import async_engine_from_config, AsyncConnection

from dicty.config import settings
from dicty.db.model import Base
from dicty.utils import get_path_relative_to_script


def autogenerate_revisions(connection: AsyncConnection, cfg: Config):
    cfg.attributes["connection"] = connection
    command.revision(cfg, "Auto generate migrations", autogenerate=True)


async def init_database():
    alembic_cfg = Config(get_path_relative_to_script("alembic.ini"))
    scripts = os.listdir(os.path.join(alembic_cfg.get_main_option("script_location"), "versions"))
    if len(scripts) == 0:
        engine = async_engine_from_config(
            {k.lower(): v for k, v in settings.items()},
            prefix="db_config_",
        )
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.run_sync(autogenerate_revisions, alembic_cfg)


async def main() -> None:
    await init_database()

    address = f"[::]:{settings.dicty_port}"
    server = grpc.server(ThreadPoolExecutor())
    server.add_insecure_port(address)
    await server.start()
    logger.info(f"Server serving at {address}")
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(main())
