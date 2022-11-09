import struct
import base64
import sqlite3
from pathlib import Path
from typing import Union, Dict, Tuple, Coroutine, Any

from pyrogram import Client
from pyrogram.storage import FileStorage, Storage
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import User


class SessionConvertor:
    def __init__(self, session_path: Path, config: Dict, work_dir: Path):
        self.session_path = session_path
        self.app_id = config['app_id']
        self.app_hash = config['app_hash']
        self.work_dir = work_dir

    async def convert(self):
        user_data, session_data = self.__get_data_telethon_session()
        converted_sting_session = self.__get_converted_sting_session(session_data, user_data)
        await self.__delete_telethon_session()
        await self.__save_pyrogram_session_file(converted_sting_session, session_data)

    async def __get_data_telethon_session(self) -> Tuple[User, StringSession]:
        async with TelegramClient(self.session_path.__str__(), self.app_id, self.app_hash) as client:
            user_data = await client.get_me()
            string_session = StringSession.save(client.session)
            session_data = StringSession(string_session)
        return user_data, session_data

    async def __save_pyrogram_session_file(self, session_string: Union[str, Coroutine[Any, Any, str]],
                                           session_data: StringSession):
        async with Client(session_string, api_id=self.app_id, api_hash=self.app_id,
                          workdir=self.work_dir.__str__()) as client:
            user_data = await client.get_me()
            client.storage = FileStorage(self.session_path.stem, Path(self.work_dir))
            await client.storage.dc_id(session_data.dc_id)
            await client.storage.test_mode(False)
            await client.storage.auth_key(session_data.auth_key.key)
            await client.storage.user_id(user_data.id)
            await client.storage.date(0)
            await client.storage.is_bot(False)
            await client.storage.save()

    async def __delete_telethon_session(self):
        if self.session_path.exists():
            self.session_path.unlink()

    @staticmethod
    async def __get_converted_sting_session(session_data: StringSession, user_data: User) -> str:
        pack = [
            Storage.SESSION_STRING_FORMAT,
            session_data.dc_id,
            None,
            session_data.auth_key.key,
            user_data.id,
            user_data.bot
        ]
        try:
            bytes_pack = struct.pack(*pack)
        except struct.error:
            pack[0] = Storage.OLD_SESSION_STRING_FORMAT_64
            bytes_pack = struct.pack(*pack)

        encode_pack = base64.urlsafe_b64encode(bytes_pack)
        decode_pack = encode_pack.decode()
        sting_session = decode_pack.rstrip("=")
        return sting_session
