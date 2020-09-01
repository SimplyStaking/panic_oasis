import os
import pdb
from configparser import ConfigParser

def setup_env(cp_main: ConfigParser) -> None:

    # Save the current UI_HOST_PORT as the UI setup isn't handled here
    # Default to port 9000 if there isn't an option in the .env file
    UI_HOST_PORT = os.getenv('UI_HOST_PORT','9000')

    # Make sure that if there is data that it it numeric and not blank
    if (not UI_HOST_PORT.isnumeric()):
        UI_HOST_PORT = '9000'

    # Clear the .env file and append all the data to it
    with open('.env', 'w') as f:
        f.seek(0)
        f.truncate(0)
        f.write(
            'MONGO_HOST_PORT={}\n'
            'MONGO_INITDB_ROOT_USERNAME={}\n'
            'MONGO_INITDB_ROOT_PASSWORD={}\n'
            'REDIS_HOST_PORT={}\n'
            'REDIS_PASSWORD={}\n'
            'UI_HOST_PORT={}\n'.format(
                cp_main['mongo']['port'],
                cp_main['mongo']['user'],
                cp_main['mongo']['pass'],
                cp_main['redis']['port'],
                cp_main['redis']['password'],
                UI_HOST_PORT,
            )
        )