"""
    Script courtesy of Gary Lee:
    https://gist.github.com/GaryLee/d1cf2089c3a515691919
"""
import sys
import logging
import ctypes


def run_as_admin(argv=None):
    shell32 = ctypes.windll.shell32
    if argv is None and shell32.IsUserAnAdmin():
        return True

    if argv is None:
        argv = sys.argv
    if hasattr(sys, '_MEIPASS'):
        # Support pyinstaller wrapped program.
        arguments = map(str, argv[1:])
    else:
        arguments = map(str, argv)
    argument_line = u' '.join(arguments)
    executable = str(sys.executable)
    logging.info('Command line: %s %s', executable, argument_line)

    result = shell32.ShellExecuteW(None, "runas", executable, argument_line, None, 1)
    if int(result) <= 32:
        return False
    return None


if __name__ == '__main__':
    ret = run_as_admin()
    if ret is True:
        logging.debug('I have admin privilege.')
    elif ret is None:
        logging.debug('I am elevating to admin privilege.')
        input('Press ENTER to exit.')
    else:
        logging.error('Error(ret=%s): cannot elevate privilege.', ret)
