import concurrent.futures
import logging
import os
from pathlib import Path
from typing import Optional, List

from .globals import OPEN_VR_DLL
from .openvr_mod import get_available_mods


class ManifestWorker:
    """ Multi threaded search in steam apps for openvr_api.dll """
    max_workers = min(48, int(max(4, os.cpu_count())))  # Number of maximum concurrent workers
    chunk_size = 16  # Number of Manifests per worker

    @classmethod
    def update_steam_apps(cls, steam_apps: dict) -> dict:
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

        logging.debug('Using %s worker threads to search for OpenVr Api Dll in %s SteamApps in %s chunks.',
                      cls.max_workers, len(steam_apps.keys()), len(manifest_ls_chunks))

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

        return steam_apps

    @staticmethod
    def worker(manifest_ls):
        for manifest in manifest_ls:
            manifest['openVrDllPaths'] = list()
            manifest['openVrDllPathsSelected'] = list()
            manifest['openVr'] = False

            # -- Test for valid path
            try:
                if not manifest['path'] or not Path(manifest['path']).exists():
                    logging.error('Skipping app with invalid paths: %s', manifest.get('name', 'Unknown'))
                    continue
            except Exception as e:
                logging.error('Error reading path for: %s %s', manifest.get('name', 'Unknown'), e)
                continue

            # -- LookUp OpenVr Api location
            try:
                open_vr_dll_path_ls = ManifestWorker.find_open_vr_dll(Path(manifest['path']))
            except Exception as e:
                logging.error('Error locating OpenVR dll for: %s %s', manifest.get('name', 'Unknown'), e)
                continue

            if open_vr_dll_path_ls:
                # -- Add OpenVr path info
                manifest['openVrDllPaths'] = [p.as_posix() for p in open_vr_dll_path_ls]
                manifest['openVrDllPathsSelected'] = [p.as_posix() for p in open_vr_dll_path_ls]
                manifest['openVr'] = True

                for mod in get_available_mods(manifest):
                    mod.update_from_disk()

        return manifest_ls

    @staticmethod
    def find_open_vr_dll(base_path: Path) -> List[Optional[Path]]:
        open_vr_dll_ls: List[Optional[Path]] = list()
        for file in base_path.glob(f'**/{OPEN_VR_DLL}'):
            open_vr_dll_ls.append(file)

        return open_vr_dll_ls
