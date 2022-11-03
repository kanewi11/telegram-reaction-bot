import sys
import json
import random
import asyncio
import logging
import time
import traceback
import configparser
from pathlib import Path

import uvloop
from pyrogram.errors import ReactionInvalid
from pyrogram.handlers import MessageHandler
from pyrogram import Client, idle, filters, types

from config import CHANNELS, POSSIBLE_KEY_NAMES, EMOJIS


TRY_AGAIN_SLEEP = 20

BASE_DIR = Path(sys.argv[0]).parent
WORK_DIR = BASE_DIR.joinpath('sessions')

CONFIG_FILE_SUFFIXES = ('.ini', '.json')

logging.basicConfig(filename='logs.log', level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logging.info('Start reaction bot.')


async def send_reaction(client: Client, message: types.Message) -> None:
    """Handler for sending reactions"""
    emoji = random.choice(EMOJIS)
    try:
        await client.send_reaction(chat_id=message.chat.id, message_id=message.id, emoji=emoji)
    except ReactionInvalid:
        logging.warning(f'{emoji} - INVALID REACTION')


async def make_work_dir() -> None:
    """Create the sessions directory if it does not exist"""
    if WORK_DIR.exists():
        return
    WORK_DIR.mkdir()


async def get_config_files_path() -> list[Path]:
    """Take all the configuration files"""
    return [file for file in WORK_DIR.iterdir() if file.suffix.lower() in CONFIG_FILE_SUFFIXES]


async def config_from_ini_file(file_path: Path) -> dict:
    """Pull the config from the *.ini file"""
    config_parser = configparser.ConfigParser()
    config_parser.read(file_path)
    section = config_parser.sections()[0]
    return {**config_parser[section]}


async def config_from_json_file(file_path: Path) -> dict:
    """Pull the config from the *.json file"""
    with open(file_path) as f:
        return json.load(f)


async def get_config(file_path: Path) -> dict:
    """Return the config file to the path"""
    config = {
        'ini': config_from_ini_file,
        'json': config_from_json_file,
    }
    extension = file_path.suffix.lower()[1:]
    config = await config[extension](file_path)
    normalized_confing = {'name': file_path.name.split('.')[0]}
    for key, values in POSSIBLE_KEY_NAMES.items():
        for value in values:
            if not config.get(value):
                continue
            normalized_confing[key] = config[value]
            break
    return normalized_confing


async def create_clients(config_files: list[Path]) -> list[Client]:
    """
    Create 'Client' instances from config files.
    **If there is no name key in the config file, then the config file has the same name as the session!**
    """
    clients = []
    for config_file in config_files:
        try:
            config_dict = await get_config(config_file)
            clients.append(Client(workdir=WORK_DIR.__str__(), **config_dict))
        except Exception:
            logging.warning(traceback.format_exc())
    return clients


async def main():
    """
    Main function:
        - Create a directory of sessions if not created.
        - Take all config files (*.json, *.ini)
        - Create clients by their config files.
        - Run through clients, add handler, start and join chat
        - Wait for completion and finish (infinitely)
    """

    await make_work_dir()
    config_files = await get_config_files_path()

    apps = await create_clients(config_files)
    if not apps:
        raise ValueError('Нет клиентов!')

    for app in apps:
        message_handler = MessageHandler(send_reaction, filters=filters.chat(CHANNELS))
        app.add_handler(message_handler)

        await app.start()

        for channel in CHANNELS:
            await app.join_chat(channel)

    await idle()

    for app in apps:
        await app.stop()


def start():
    """Let's start"""
    uvloop.install()
    try:
        asyncio.run(main())
    except Exception:
        logging.critical(traceback.format_exc())

    logging.info(f'Waiting {TRY_AGAIN_SLEEP} sec. before restarting the program...')
    time.sleep(TRY_AGAIN_SLEEP)


if __name__ == '__main__':
    start()
