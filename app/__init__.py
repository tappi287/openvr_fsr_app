from .app_main import expose_main
from .valve.steam import SteamApps


def expose_app_methods():
    expose_main()
