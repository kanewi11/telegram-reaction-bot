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

Bot puts reaction to new posts in the channel, group or chat. Reactions are set from all connected sessions, as well as automatic subscription to channels from these sessions!

**Good stuff 👍:**
* Automatically converts `TDATA to a Pyrogram session`.
* Automatically converts a `Telethon session to a Pyrogram session`.

## Launch Instructions
1. Create an empty directory
2. `git clone https://github.com/kanewi11/telegram-reaction-bot.git ./`.
3. `python3 -m venv venv` or on windows `python -m venv venv`.
4. `. venv/bin/activate` or on windows `\venv\Scripts\activate`.
5. `pip install -r requirements.txt` or in windows `pip install -r requirements_win.txt`.
6. Add your channel name to `config.py`.
7. **If you plan to use the TDATA converter**, go to `converters/tdata_to_telethon.py` and insert your `API_HASH` and `API_ID` (lines 19 and 20).
8. `mkdir sessions` and `mkdir tdatas` _(or just create these two folders)_
9. Add the session file and its configuration file to the `/sessions` directory ( _which we created in step 8_ ) or tdata files to the `/tdatas` folder (**Note the 7th point**). 
Here is an example:

   ```
      your_dir
      └───reactionbot.py
      │
      └───sessions
      │   │   8888888888.ini
      │   │   8888888888.session
      │   │   9999999999.ini
      │   │   9999999999.session
      │   │   98767242365.json
      │   │   98767242365.session
      │   │   ...
      │
      └───tdatas
      │   └─── my_tdata
      │   │   │ key_datas
      │   │   │ ...
      ...
   ```
10. `nohup python reactionbot.py &`

## Create a session file manually.
Create a file `my_account.json` ( _the file name can be anything_ ) in the directory `/sessions` :
```
{
    "api_id": "your_api_id",
    "api_hash": "your_api_hash",
    "phone_number": "your_phone_number"
}
```

After `python reactionbot.py`, in the console go through the account authorization steps and that's it, the session file will be created, you don't need to do this for the next times.

## Where do I get `api_id` and `api_hash`?
[🔗 Click me.](https://my.telegram.org/auth)

## Sample configuration file
You can add more parameters that [pyrogram](https://github.com/pyrogram/pyrogram) supports.

`sessions/888888888.ini`
```
[pyrogram]
api_id = your_api_id
api_hash = your_api_hash
phone_number = 888888888

# optional parameters
app_version = '8.8.5'
device_model = 'Vertu IVERTU'
system_version = 'Android'
```

**OR** ( select one of the variants of the configuration file )

`sessions/888888888.json`
```
{
    "api_id": "your_api_id",
    "api_hash": "your_api_hash",
    "phone_number": "your_phone_number",
    ...
}
```
