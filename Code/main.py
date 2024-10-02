import argparse
import asyncio
import logging
import os
import platform
import subprocess
import sys
from pathlib import Path

from api import ChatServerModule, DownloadServerModule, UserServerModule
from DMBotNetwork import Server
from dotenv import load_dotenv
from root_path import ROOT_PATH
from systems.file_work import Settings

load_dotenv()


class FixedWidthFormatter(logging.Formatter):
    def format(self, record):
        record.levelname = f"{record.levelname:<7}"
        return super().format(record)

def init_all() -> None:
    logging.info("Initialize main_app_settings.json...")
    Settings.load()
    Settings.init_base_settings(
        {
            "app": {
                "host": "localhost",
                "port": 5000,
                "timeout": 30.0,
                "allow_registration": True,
                "server_name": "dev",
                "max_players": 25,
            }
        }
    )
    logging.info("Done")

    logging.info("Initialize Server modules...")
    Server()

    Server.register_methods_from_class(
        [DownloadServerModule, UserServerModule, ChatServerModule]
    )
    logging.info("Done")


async def main() -> None:
    base_access_flags = {
        "access_admin_chat": False,
        "change_access": False,
        "change_password": True,
        "change_server_settings": False,
        "create_users": False,
        "delete_users": False,
    }

    env_password = os.getenv("OWNER_PASSWORD")
    base_owener_password = env_password if env_password else "owner_password"

    await Server.setup_server(
        server_name=Settings.get_s("app.server_name"),
        host=Settings.get_s("app.host"),
        port=Settings.get_s("app.port"),
        db_path=Path(ROOT_PATH / "data"),
        init_owner_password=base_owener_password,
        base_access=base_access_flags,
        allow_registration=Settings.get_s("app.allow_registration"),
        timeout=Settings.get_s("app.timeout"),
        max_player=Settings.get_s("app.max_players"),
    )

    await Server.start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Запуск сервера DMBot")
    parser.add_argument("--debug", action="store_true", help="Включение режима отладки")

    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO

    handler = logging.StreamHandler()
    formatter = FixedWidthFormatter(
        "[%(asctime)s][%(levelname)s] %(name)s: %(message)s"
    )

    handler.setFormatter(formatter)

    logging.basicConfig(
        level=log_level,
        handlers=[handler],
    )

    init_all()

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        logging.info("Server shutdown initiated by user.")
