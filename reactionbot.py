import json
import time
import random
import asyncio
import logging
import platform
import traceback
import configparser
from pathlib import Path
from sqlite3 import OperationalError
from typing import List, Dict, Union

from pyrogram.errors import ReactionInvalid, UserNotParticipant
from pyrogram.handlers import MessageHandler
from pyrogram import Client, idle, filters, types
from pyrogram.errors.exceptions.unauthorized_401 import UserDeactivatedBan

from config import CHANNELS, POSSIBLE_KEY_NAMES, EMOJIS
from converters import SessionConvertor, convert_tdata


if platform.system() != 'Windows':
    import uvloop
    uvloop.install()


TRY_AGAIN_SLEEP = 20

BASE_DIR = Path(__file__).parent
WORK_DIR = BASE_DIR.joinpath('sessions')
LOGS_DIR = BASE_DIR.joinpath('logs')
TDATAS_DIR = BASE_DIR.joinpath('tdatas')
SUCCESS_CONVERT_TDATA_DIR = TDATAS_DIR.joinpath('success')
UNSUCCESSFUL_CONVERT_TDATA_DIR = TDATAS_DIR.joinpath('unsuccessful')

BANNED_SESSIONS_DIR = WORK_DIR.joinpath('banned_sessions')
UNNECESSARY_SESSIONS_DIR = WORK_DIR.joinpath('unnecessary_sessions')

CONFIG_FILE_SUFFIXES = ('.ini', '.json')

LOGS_DIR.mkdir(exist_ok=True)

loggers = ['info', 'error']
formatter = logging.Formatter('%(name)s %(asctime)s %(levelname)s %(message)s')

this_media_id = None

for logger_name in loggers:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    log_filepath = LOGS_DIR.joinpath(f'{logger_name}.log')
    handler = logging.FileHandler(log_filepath)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.warning('Start reaction bot.')

error = logging.getLogger('error')
info = logging.getLogger('info')

apps = []
sent = []


async def send_reaction(client: Client, message: types.Message) -> None:
    """Handler for sending reactions"""
    emoji = random.choice(EMOJIS)
    try:
        random_sleep_time = random.randint(1, 5)
        await asyncio.sleep(random_sleep_time)
        await client.send_reaction(chat_id=message.chat.id, message_id=message.id, emoji=emoji)
    except ReactionInvalid:
        error.warning(f'{emoji} - invalid reaction')
    except UserDeactivatedBan:
        error.warning(f'Session banned - {client.name}')
    except Exception:
        error.warning(traceback.format_exc())
    else:
        info.info(f'Session {client.name} send - {emoji}')


async def send_reaction_from_all_applications(_, message: types.Message) -> None:
    """
    What is it for? Why not just assign a handler function to each app?

    The answer is simple, if several sessions have the same API_ID and API_HASH,
    only one of those sessions will send a response!
    """

    global this_media_id  # sorry :)

    post = (message.chat.id, message.id)
    if post in sent:
        return
    sent.append(post)

    if this_media_id == message.media_group_id and message.media_group_id is not None:
        return

    this_media_id = message.media_group_id

    for app, _, _ in apps:
        await send_reaction(app, message)


async def get_chat_id(app: Client, chat_link: str) -> Union[int, str, None]:
    """Return chat_id or None or raise AttributeError"""
    try:
        chat = await app.get_chat(chat_link)
    except:
        return None
    else:
        return chat.id


async def is_subscribed(app: Client, chat_link: str) -> bool:
    """Check if the channel is subscribed"""
    try:
        chat_id = await get_chat_id(app, chat_link)
        if chat_id is None:
            return False
        await app.get_chat_member(chat_id, 'me')
    except (UserNotParticipant, AttributeError):
        return False
    else:
        return True


async def make_work_dir() -> None:
    """Create the sessions directory if it does not exist"""
    WORK_DIR.mkdir(exist_ok=True)
    UNNECESSARY_SESSIONS_DIR.mkdir(exist_ok=True)
    BANNED_SESSIONS_DIR.mkdir(exist_ok=True)
    TDATAS_DIR.mkdir(exist_ok=True)
    SUCCESS_CONVERT_TDATA_DIR.mkdir(exist_ok=True)
    UNSUCCESSFUL_CONVERT_TDATA_DIR.mkdir(exist_ok=True)


async def get_config_files_path() -> List[Path]:
    """Take all the configuration files"""
    return [file for file in WORK_DIR.iterdir() if file.suffix.lower() in CONFIG_FILE_SUFFIXES]


async def config_from_ini_file(file_path: Path) -> Dict:
    """Pull the config from the *.ini file"""
    config_parser = configparser.ConfigParser()
    config_parser.read(file_path)
    section = config_parser.sections()[0]
    return {**config_parser[section]}


async def config_from_json_file(file_path: Path) -> Dict:
    """Pull the config from the *.json file"""
    with open(file_path) as f:
        return json.load(f)


async def get_config(file_path: Path) -> Dict:
    """Return the config file to the path"""
    config_suffixes = {
        '.ini': config_from_ini_file,
        '.json': config_from_json_file,
    }
    suffix = file_path.suffix.lower()
    config = await config_suffixes[suffix](file_path)
    normalized_confing = {'name': file_path.stem}
    for key, values in POSSIBLE_KEY_NAMES.items():
        for value in values:
            if not config.get(value):
                continue
            normalized_confing[key] = config[value]
            break
    return normalized_confing


async def create_apps(config_files_paths: List[Path]) -> None:
    """
    Create 'Client' instances from config files.
    **If there is no name key in the config file, then the config file has the same name as the session!**
    """
    for config_file_path in config_files_paths:
        try:
            config_dict = await get_config(config_file_path)
            session_file_path = WORK_DIR.joinpath(config_file_path.with_suffix('.session'))
            apps.append((Client(workdir=WORK_DIR.__str__(), **config_dict), config_dict, session_file_path))
        except Exception:
            error.warning(traceback.format_exc())


async def try_convert(session_path: Path, config: Dict) -> bool:
    """Try to convert the session if the session failed to start in Pyrogram"""
    convertor = SessionConvertor(session_path, config, WORK_DIR)
    try:
        await convertor.convert()
    except OperationalError:
        if session_path.exists():
            await convertor.move_file_to_unnecessary(session_path)
        for suffix in CONFIG_FILE_SUFFIXES:
            config_file_path = session_path.with_suffix(suffix)
            if config_file_path.exists():
                await convertor.move_file_to_unnecessary(config_file_path)
        error.warning(f'Preservation of the session failed {session_path.stem}')
        return False
    except Exception:
        error.warning(traceback.format_exc())
        return False
    else:
        return True


def get_tdatas_paths() -> List[Path]:
    """Get paths to tdata dirs"""
    reserved_dirs = [SUCCESS_CONVERT_TDATA_DIR, UNSUCCESSFUL_CONVERT_TDATA_DIR]
    return [path for path in TDATAS_DIR.iterdir() if path not in reserved_dirs]


async def move_session_to_ban_dir(session_path: Path):
    """Move file to ban dir"""

    if session_path.exists():
        await move_file(session_path, BANNED_SESSIONS_DIR)

    for suffix in CONFIG_FILE_SUFFIXES:
        config_file_path = session_path.with_suffix(suffix)
        if not config_file_path.exists():
            continue
        await move_file(config_file_path, BANNED_SESSIONS_DIR)


async def move_file(path_from: Path, path_to: Path):
    """File or directory relocation"""
    path_from.rename(path_to.joinpath(path_from.name))


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

    tdatas_paths = get_tdatas_paths()
    for tdata_path in tdatas_paths:
        try:
            await convert_tdata(tdata_path, WORK_DIR)
        except Exception:
            error.warning(traceback.format_exc())
            await move_file(tdata_path, UNSUCCESSFUL_CONVERT_TDATA_DIR)
        else:
            await move_file(tdata_path, SUCCESS_CONVERT_TDATA_DIR)

    config_files = await get_config_files_path()
    await create_apps(config_files)
    if not apps:
        raise Exception('No apps!')

    message_handler = MessageHandler(send_reaction_from_all_applications, filters=filters.chat(CHANNELS))
    for app, config_dict, session_file_path in apps:
        app.add_handler(message_handler)

        try:
            await app.start()
        except OperationalError:
            is_converted = await try_convert(session_file_path, config_dict)
            apps.remove((app, config_dict, session_file_path))
            if not is_converted:
                info.info(f'Did not convert - {app.name}')
                continue
            try:
                app = Client(workdir=WORK_DIR.__str__(), **config_dict)
                app.add_handler(message_handler)
                await app.start()

            except Exception:
                error.warning(traceback.format_exc())
            else:
                apps.append((app, config_dict, session_file_path))
        except UserDeactivatedBan:
            await move_session_to_ban_dir(session_file_path)
            error.warning(f'Session banned - {app.name}')
            apps.remove((app, config_dict, session_file_path))
            continue
        except Exception:
            apps.remove((app, config_dict, session_file_path))
            error.warning(traceback.format_exc())
            continue

        info.info(f'Session started - {app.name}')
        for channel in CHANNELS:
            subscribed = await is_subscribed(app, channel)
            if not subscribed:
                random_sleep_time = random.randint(1, 10)
                await asyncio.sleep(random_sleep_time)
                await app.join_chat(channel)
                info.info(f'{app.name} joined - "@{channel}"')

    if not apps:
        raise Exception('No apps!')

    info.warning('All sessions started!')
    await idle()

    for app, _, _ in apps:
        try:
            info.warning(f'Stopped - {app.name}')
            await app.stop()
        except ConnectionError:
            pass
    apps[:] = []


def start():
    """Let's start"""
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except Exception:
        error.critical(traceback.format_exc())
        error.warning(f'Waiting {TRY_AGAIN_SLEEP} sec. before restarting the program...')
        time.sleep(TRY_AGAIN_SLEEP)


if __name__ == '__main__':
    while True:
        start()
