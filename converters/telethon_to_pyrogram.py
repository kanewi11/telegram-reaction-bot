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
        if work_dir is None:
            work_dir = Path(__file__).parent.parent.joinpath('sessions')
        self.session_path = session_path if session_path else work_dir
        self.inappropriate_sessions_path = work_dir.joinpath('unnecessary_sessions')
        self.api_id = config['api_id'] if config else None
        self.api_hash = config['api_hash'] if config else None
        self.work_dir = work_dir

    async def convert(self) -> None:
        """Main func"""
        user_data, session_data = await self.__get_data_telethon_session()
        converted_sting_session = await self.get_converted_sting_session(session_data, user_data)
        await self.move_file_to_unnecessary(self.session_path)
        await self.save_pyrogram_session_file(converted_sting_session, session_data)

    async def move_file_to_unnecessary(self, file_path: Path):
        """Move the unnecessary Telethon session file to the directory with the unnecessary sessions"""
        if file_path.exists():
            file_path.rename(self.inappropriate_sessions_path.joinpath(file_path.name))

    async def __get_data_telethon_session(self) -> Tuple[User, StringSession]:
        """Get User and StringSession"""
        async with TelegramClient(self.session_path.with_suffix('').__str__(), self.api_id, self.api_hash) as client:
            user_data = await client.get_me()
            string_session = StringSession.save(client.session)
            session_data = StringSession(string_session)
            return user_data, session_data

    async def save_pyrogram_session_file(self, session_string: Union[str, Coroutine[Any, Any, str]],
                                         session_data: StringSession):
        """Create session file for pyrogram"""
        async with Client(self.session_path.stem, session_string=session_string, api_id=self.api_id,
                          api_hash=self.api_hash, workdir=self.work_dir.__str__()) as client:
            user_data = await client.get_me()
            client.storage = FileStorage(self.session_path.stem, self.work_dir)
            client.storage.conn = sqlite3.Connection(self.session_path)
            client.storage.create()
            await client.storage.dc_id(session_data.dc_id)
            await client.storage.test_mode(False)
            await client.storage.auth_key(session_data.auth_key.key)
            await client.storage.user_id(user_data.id)
            await client.storage.date(0)
            await client.storage.is_bot(False)
            await client.storage.save()

    @staticmethod
    async def get_converted_sting_session(session_data: StringSession, user_data: User) -> str:
        """Convert to sting session"""
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
        return decode_pack.rstrip("=")
