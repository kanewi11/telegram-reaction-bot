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

uvloop.install()

logging.basicConfig(filename='logs.log', level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logging.info('Start reaction bot.')

BASE_DIR = Path(sys.argv[0]).parent
WORK_DIR = BASE_DIR.joinpath('sessions')
CONFIG_FILE_SUFFIXES = ('.ini', '.json')


async def send_reaction(client: Client, message: types.Message) -> None:
    """Хендлер для отправки реакций"""
    emoji = random.choice(EMOJIS)
    try:
        await client.send_reaction(chat_id=message.chat.id, message_id=message.id, emoji=emoji)
    except ReactionInvalid:
        logging.warning(f'{emoji} - INVALID REACTION')


async def make_work_dir() -> None:
    """Создаем директорию sessions если ее нет"""
    if WORK_DIR.exists():
        return
    WORK_DIR.mkdir()


async def get_config_files_path() -> list[Path]:
    """Берем все конфиг файлы"""
    return [file for file in WORK_DIR.iterdir() if file.suffix.lower() in CONFIG_FILE_SUFFIXES]


async def config_from_ini_file(file_path: Path) -> dict:
    """Вытаскиваем конфиг из *.ini файла"""
    config_parser = configparser.ConfigParser()
    config_parser.read(file_path)
    section = config_parser.sections()[0]
    return {**config_parser[section]}


async def config_from_json_file(file_path: Path) -> dict:
    """Вытаскиваем конфиг из *.json файла"""
    with open(file_path) as f:
        return json.load(f)


async def get_config(file_path: Path) -> dict:
    """Возвращаем конфиг файл по пути"""
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
    Создаем экземпляры 'Client' из конфиг файлов.
    **Если в конфиг файле нет ключа name, то конфиг файл нужно назвать так же как и сессию!**
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
    Главная функция:
        - Создаем директорию sessions если не создана.
        - Берем все конфиг файлы (*.json, *.ini)
        - Создаем по конфиг файлам клиентов
        - Пробегаемся по клиентам, добавляем handler, стартуем, а так же присоединяемся к чату
        - Ждем завершения и завершаем (бесконечно)
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


if __name__ == '__main__':
    while True:
        try:
            asyncio.run(main())
        except Exception:
            logging.critical(traceback.format_exc())

        logging.info(f'Ожидание {TRY_AGAIN_SLEEP} сек до повторного запуска программы')
        time.sleep(TRY_AGAIN_SLEEP)
