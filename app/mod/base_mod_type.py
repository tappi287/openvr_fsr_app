class BaseModType:
    invalid = -1
    fsr = 0
    foveated = 1
    vrp = 2

    mod_types = {0: 'FsrMod', 1: 'FoveatedMod', 2: 'VRPerfKitMod'}
    mod_data_dir_names = {0: 'openvr_fsr', 1: 'openvr_foveated', 2: 'vrperfkit'}
