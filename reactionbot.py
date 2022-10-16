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
from pyrogram import Client, idle, filters, types
from pyrogram.handlers import MessageHandler

from config import channels


ERROR_SLEEP = 20

uvloop.install()

logging.basicConfig(filename='logs.log', level=logging.INFO)
logging.info('Start reaction bot.')

BASE_DIR = Path(sys.argv[0]).parent
WORK_DIR = BASE_DIR.joinpath('sessions')
CONFIG_FILE_EXTENSION = ('ini', 'json')

possible_key_names = {
    'api_id': ['api_id', 'app_id'],
    'api_hash': ['api_hash', 'app_hash'],
    'app_version': ['app_version'],
    'device_model': ['device_model', 'device'],
    'system_version': ['system_version', 'sdk'],
    'phone_number': ['phone_number', 'phone']
}

emojis = ['👍', '❤️', '🔥', '🥰', '👏', '😁', '🤔', '🤯', '🎉', '🤩', '⚡️', '💯', '❤️‍🔥', '🙏🏻']


async def send_reaction(client: Client, message: types.Message) -> None:
    """Хендлер для отправки реакций"""
    emoji = random.choice(emojis)
    await client.send_reaction(chat_id=message.chat.id, message_id=message.id, emoji=emoji)


async def make_work_dir() -> None:
    """Создаем директорию sessions если ее нет"""
    if WORK_DIR.exists():
        return
    WORK_DIR.mkdir()


async def get_config_files_path() -> list[Path]:
    """Берем все конфиг файлы"""
    return [file for file in WORK_DIR.iterdir() if file.suffix.lower()[1:] in CONFIG_FILE_EXTENSION]


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
    for key, values in possible_key_names.items():
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
        message_handler = MessageHandler(send_reaction, filters=filters.chat(channels))
        app.add_handler(message_handler)

        await app.start()

        for channel in channels:
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

        logging.info(f'Ожидание {ERROR_SLEEP} сек до повторного запуска программы')
        time.sleep(ERROR_SLEEP)
