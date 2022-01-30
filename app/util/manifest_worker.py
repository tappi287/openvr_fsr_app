import threading
from queue import Queue
import concurrent.futures
import logging
import os
from pathlib import Path
from typing import Optional, List

import gevent

from app.globals import OPEN_VR_DLL, EXE_NAME
from app.mod import get_available_mods
from app.events import progress_update


def run_update_steam_apps(steam_apps: dict) -> dict:
    """ Calls ManifestWorker.update_steam_apps from thread to not block the event loop """
    q = Queue()
    t = threading.Thread(target=ManifestWorker.update_steam_apps, args=(steam_apps, q))
    t.start()

    # -- Wait for thread to finish
    while t.is_alive():
        gevent.sleep(1)
        t.join(timeout=0.1)

    return q.get()


class ManifestWorker:
    """ Multithreading powered search in apps dict for openvr_api.dll and executable paths """
    max_workers = min(48, int(max(4, os.cpu_count())))  # Number of maximum concurrent workers
    chunk_size = 16  # Number of Manifests per worker

    @classmethod
    def update_steam_apps(cls, steam_apps: dict, queue: Queue = None) -> dict:
        app_id_list = list(steam_apps.keys())

        # -- Split server addresses into chunks for workers
        manifest_ls_chunks = list()
        while app_id_list:
            # -- Create a list of chunk size number of AppIds
            id_chunk_ls = list()
            for i in range(min(cls.chunk_size, len(app_id_list))):
                id_chunk_ls.append(app_id_list.pop())

            # -- Append a list of manifests to search thru in this chunk
            manifest_ls_chunks.append(
                [steam_apps.get(app_id) for app_id in id_chunk_ls]
            )

        logging.debug('Using maximum of %s worker threads to search thru %s Apps in %s chunks.',
                      cls.max_workers, len(steam_apps.keys()), len(manifest_ls_chunks))
        progress = 0
        progress_update(f'{progress} / {len(steam_apps.keys())}')

        with concurrent.futures.ThreadPoolExecutor(max_workers=cls.max_workers) as executor:
            future_info = {
                executor.submit(cls.worker, manifest_ls): manifest_ls for manifest_ls in manifest_ls_chunks
            }

            for future in concurrent.futures.as_completed(future_info):
                manifest_chunk = future_info[future]
                try:
                    manifest_ls = future.result()
                except Exception as exc:
                    if len(manifest_chunk):
                        logging.error('Chunk %s generated an exception: %s', manifest_chunk[0].get('name'), exc)
                    else:
                        logging.error('Worker generated an exception: %s', exc)
                else:
                    if not manifest_ls:
                        continue

                    # -- Update SteamApp entries
                    for manifest in manifest_ls:
                        steam_apps[manifest.get('appid')] = manifest

                    # -- Update Progress
                    progress += len(manifest_ls)
                    manifest = manifest_ls[-1:][0]
                    progress_update(f'{manifest.get("path", " ")[0:2]} {progress} / {len(steam_apps.keys())}')

        if queue is not None:
            queue.put(steam_apps)

        return steam_apps

    @staticmethod
    def worker(manifest_ls):
        for manifest in manifest_ls:
            manifest['openVr'] = False

            # -- Test for valid path
            try:
                if not manifest['path'] or not Path(manifest['path']).exists():
                    logging.error('Skipping app with invalid paths: %s', manifest.get('name', 'Unknown'))
                    continue
            except Exception as e:
                logging.error('Error reading path for: %s %s', manifest.get('name', 'Unknown'), e)
                continue

            progress_update(f'{manifest["path"][0:2]} {Path(manifest["path"]).stem}')

            # -- LookUp OpenVr Api location(s)
            try:
                open_vr_dll_path_ls = ManifestWorker.find_open_vr_dll(Path(manifest['path']))
                # -- Add OpenVr path info
                manifest['openVrDllPaths'] = [p.as_posix() for p in open_vr_dll_path_ls]
                manifest['openVrDllPathsSelected'] = [p.as_posix() for p in open_vr_dll_path_ls]
            except Exception as e:
                logging.error('Error locating OpenVR dll for: %s %s', manifest.get('name', 'Unknown'), e)
                continue

            # -- LookUp Executable location(s)
            try:
                executable_path_ls = ManifestWorker.find_executables(Path(manifest['path']))
                # -- Add executables path info
                manifest['executablePaths'] = [p.as_posix() for p in executable_path_ls]
                manifest['executablePathsSelected'] = [p.as_posix() for p in executable_path_ls]
            except Exception as e:
                logging.error('Error locating Executables for: %s %s', manifest.get('name', 'Unknown'), e)
                continue

            if open_vr_dll_path_ls:
                manifest['openVr'] = True

            if open_vr_dll_path_ls or executable_path_ls:
                for mod in get_available_mods(manifest):
                    read_result = mod.update_from_disk()

                    if not read_result:
                        manifest[mod.VAR_NAMES['settings']] = mod.settings.to_js(export=True)
                        manifest[mod.VAR_NAMES['installed']] = manifest.get(mod.VAR_NAMES['installed'], False)
                        manifest[mod.VAR_NAMES['version']] = manifest.get(mod.VAR_NAMES['version'], '')

        return manifest_ls

    @staticmethod
    def find_open_vr_dll(base_path: Path) -> List[Optional[Path]]:
        open_vr_dll_ls: List[Optional[Path]] = list()
        for file in base_path.glob(f'**/{OPEN_VR_DLL}'):
            open_vr_dll_ls.append(file)

        return open_vr_dll_ls

    @staticmethod
    def find_executables(base_path: Path) -> List[Optional[Path]]:
        executable_ls: List[Optional[Path]] = list()
        for file in base_path.glob(f'**/{EXE_NAME}'):
            executable_ls.append(file)

        return executable_ls
