import logging
import os
import webbrowser
from pathlib import Path

import eel

from app.app_main import close_request
from app.app_settings import AppSettings
from app.globals import get_current_modules_dir


def start_in_browser(npm_serve=True):
    page = 'index.html'
    host = 'localhost'
    port = 8144

    if npm_serve:
        # Dev env with npm run serve
        page = {'port': 8080}
        url_port = page.get('port')
        eel.init(Path(get_current_modules_dir()).joinpath('src').as_posix())
    else:
        # Frozen or npm run build
        url_port = port
        eel.init(Path(get_current_modules_dir()).joinpath('web').as_posix())

    edge_cmd = f"{os.path.expandvars('%PROGRAMFILES(x86)%')}\\Microsoft\\Edge\\Application\\msedge.exe"
    start_url = f'http://{host}:{url_port}'
    logging.debug(f'Preparing Browser start: {start_url}/{page}')
    if Path(edge_cmd).exists():
        logging.debug(f'Found Edge: {edge_cmd}')
    else:
        logging.debug(f'Edge not found: {edge_cmd}')

    try:
        app_module_prefs = getattr(AppSettings, 'app_preferences', dict()).get('appModules', list())
        if Path(edge_cmd).exists() and 'edge_preferred' in app_module_prefs:
            logging.debug('Starting in Edge.')
            eel.start(page, mode='custom', host=host, port=port, block=False,
                      cmdline_args=[edge_cmd, '--profile-directory=Default', f'--app={start_url}'])
        else:
            logging.debug('Starting in Chrome.')
            eel.start(page, host=host, port=port, block=False, close_callback=close_request)
    except EnvironmentError:
        # If Chrome isn't found, fallback to Microsoft Chromium Edge
        if Path(edge_cmd).exists():
            logging.info('Falling back to Edge Browser')
            eel.start(page, mode='custom', host=host, port=port, block=False,
                      cmdline_args=[edge_cmd, '--profile-directory=Default', f'--app={start_url}'])
        # Fallback to opening a regular browser window
        else:
            logging.info('Falling back to default Web Browser')
            eel.start(page, mode=None, app_mode=False, host=host, port=port, block=False)
            # Open system default web browser
            webbrowser.open_new(start_url)
    logging.debug('Browser Start finished')
