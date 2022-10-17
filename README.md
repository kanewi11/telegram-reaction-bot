## Bot for posting reactions to a Telegram post.

<p align="center">
   <a href="https://telegram.org" target="_blank">
      <img width="50" src="https://telegram.org/img/website_icon.svg?4" alt="Telegram">
   </a>   
   &nbsp;&nbsp;&nbsp;&nbsp;
   <a href="https://github.com/pyrogram/pyrogram" target="_blank">
      <img width="35" src="https://camo.githubusercontent.com/23bd8586f8d0549172b03886618d5337c7c3f655220d81d35ce837b62639419d/68747470733a2f2f646f63732e7079726f6772616d2e6f72672f5f7374617469632f7079726f6772616d2e706e67" alt="Pyrogram">
   </a>
</p>

**This script sends reactions to a new post or message in selected open groups and channels, as well as automatically subscribes to them.**

## Launch Instructions
1. Create an empty directory
2. `git clone https://github.com/kanewi11/telegram-reaction-bot.git ./`
3. `python3 -m venv venv`
4. `source venv/bin/activate`
5. `pip install -r requirements.txt`
6. Add your channel name to `config.py`
7. `mkdir sessions`
8. **Sessions must be for [pyrogram](https://github.com/pyrogram/pyrogram)!** 

    Add the session file and its configuration file to the /sessions directory ( _which we created in step 7_ ). 

    **These two files must have the same name!** Here is an example:

    ```
   you_dir
   └───sessions
   │   │   8888888888.ini
   │   │   8888888888.session
   │   │   9999999999.ini
   │   │   9999999999.session
   │   │   98767242365.json
   │   │   98767242365.session
   ...
    ```
9. `nohup python reactionbot.py &`


## Sample configuration file *.ini
You can add more parameters that [pyrogram](https://github.com/pyrogram/pyrogram) supports.
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
You can add more parameters that [pyrogram](https://github.com/pyrogram/pyrogram) supports.
```
{
    "api_id": "you_api_id",
    "api_hash": "you_api_hash",
    ...
}
```

### TODO:
 - If there will be time to add session definition and conversion from tdata, telethon.
But I don't think the time will come 🙃.