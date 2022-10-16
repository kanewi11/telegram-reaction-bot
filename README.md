# Bot for posting reactions to a Telegram post.
**Bot puts reactions only to new posts!**

## Launch Instructions:
1. Create an empty directory
2. `git clone https://github.com/kanewi11/telegram-reaction-bot.git ./`
3. `python3 -m venv venv`
4. `source venv/bin/activate`
5. `pip install -r requirements.txt`
6. Add your channel name to `config.py`
7. `mkdir sessions`
8. **Sessions must be for Pyrogram!** Add the session file and its configuration file to the `/sessions` directory. **These two files must have the same name!** Here is an example:
```
/sessions
│   8888888888.ini
│   8888888888.session
│   9999999999.ini
│   9999999999.session
│   98767242365.json
│   98767242365.session
```
9. `nohup python reactionbot.py &`


## Sample configuration file *.ini
You can add more parameters that Pyrogram supports.
```
[pyrogram]
api_id = you_api_id
api_hash = you_api_hash	

# optional parameters
app_version = '8.8.5'
device_model = 'Vertu IVERTU'
system_version = 'Android'
```

## Sample configuration file *.json
You can add more parameters that Pyrogram supports.
```
{
    "api_id": "you_api_id",
    "api_hash": "you_api_hash",
    ...
}
```