import os
from shared_database.config import get_database_config

config = get_database_config()
print('Sync URL:', config.database_url)
print('Async URL:', config.async_database_url)
