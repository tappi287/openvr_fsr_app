import logging
import os
import webbrowser
from pathlib import Path

import eel

from app.app_main import close_request
from app.app_settings import BrowserSettings as bs
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
    use_system_web_browser = False

    # -- Browser availability
    if bs.no_browser_available():
        raise RuntimeError('Found no Web-Browser available on this System to start in. You may delete your app '
                           'settings in %LOCALAPPDATA%/openvr_fsr_app and try to run the app again.')

    logging.debug(f'Preparing Browser start: {start_url}/{page}')
    if Path(edge_cmd).exists():
        logging.debug(f'Found Edge: {edge_cmd}')
    else:
        logging.debug(f'Edge not found: {edge_cmd}')
    if bs.is_browser_available(bs.TYPE_EDGE):
        logging.info('Edge Browser available according to saved AppSettings.')
    elif bs.is_browser_available(bs.TYPE_CHROME):
        logging.info('Chrome Browser available according to saved AppSettings.')

    # -- Start
    try:
        if Path(edge_cmd).exists() and bs.is_browser_available(bs.TYPE_EDGE):
            bs.CURRENT_BROWSER = bs.TYPE_EDGE
            logging.debug('Starting in Edge in App Mode.')
            eel.start(page, mode='custom', host=host, port=port, block=False,
                      cmdline_args=[edge_cmd, '--profile-directory=Default', f'--app={start_url}'])
        elif bs.is_browser_available(bs.TYPE_CHROME):
            bs.CURRENT_BROWSER = bs.TYPE_CHROME
            logging.debug('Starting in Chrome in App Mode.')
            eel.start(page, host=host, port=port, block=False, close_callback=close_request)
    except EnvironmentError as e:
        logging.error(f'Browser start failed, trying in system web-browser: {e}')
        use_system_web_browser = True

    # -- System web-browser fallback
    if not bs.is_browser_available(bs.TYPE_EDGE) and not bs.is_browser_available(bs.TYPE_CHROME):
        use_system_web_browser = True

    if use_system_web_browser:
        bs.CURRENT_BROWSER = bs.TYPE_SYSTEM_BROWSER
        logging.debug('Starting in system web-browser.')

        logging.info('Falling back to default Web Browser')
        eel.start(page, mode=None, app_mode=False, host=host, port=port, block=False)
        # Open system default web browser
        webbrowser.open_new(start_url)

    logging.debug('Browser Start finished')
