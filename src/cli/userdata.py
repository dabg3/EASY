import os
import pathlib
import base64
import collections.abc
import hashlib

class UnsafeFileStore:

    # A file is created for each address, having filename as sha256(address).
    # Content is base64-encoded, it can be anything.

    def __init__(self, path: str = None):
        if not path:
            path = get_system_userdata_path()
        dir_path = pathlib.Path(path)
        if not dir_path.exists():
            raise ValueError(f"directory does not exist: {path}")
        if not dir_path.is_dir():
            raise ValueError(f"not a directory: {path}")
        self._datapath = dir_path

    def store(self, addr: str, data: bytes):
        filename = hashlib.sha256(addr.encode()).hexdigest()
        filepath = self._datapath / filename
        v = base64.b64encode(data).decode()
        self._secure_write(filepath, v)
        
    @staticmethod
    def _secure_write(path: pathlib.Path, data: bytes):
        try:
            with open(path, 'w') as f:
                f.write(data)
        except PermissionError:
            raise PermissionError(f"restricted access: {path}")
        except OSError as e:
            raise ValueError(f"cannot write {path}: {str(e)}")

    def get(self, addr) -> bytes | None:
        filename = hashlib.sha256(addr.encode()).hexdigest()
        filepath = self._datapath / filename
        if not filepath.exists():
            return None
        with open(filepath, 'r') as f:
            data = f.read()
        return base64.b64decode(data.encode())

    def delete(self, addr: str):
        filename = hashlib.sha256(addr.encode()).hexdigest()
        filepath = self._datapath / filename
        filepath.unlink(missing_ok=True)


# TODO define on a central location then inject it
_appname = 'easy'


# TODO take a create= param 
def get_system_userdata_path() -> str: 
    """
    TODO
    """
    if os.name == 'posix':
        return _get_posix_userdata_path()
    elif os.name == 'nt':
        return _get_win_userdata_path()
    else:
        raise NotImplementedError('unknown system')
        

def _get_posix_userdata_path() -> str:
    # follows XDG Base Directory Specification, defaults to ~/.local/share/easy
    xdg_data_home = os.getenv('XDG_DATA_HOME')
    if xdg_data_home:
        data_dir = pathlib.Path(xdg_data_home) / _appname
    else:
        data_dir = pathlib.Path.home() / '.local' / 'share' / _appname
    data_dir.mkdir(parents=True, exist_ok=True)
    return str(data_dir)


def _get_win_userdata_path() -> str:
    # use %LOCALAPPDATA%, defaults to C:\\Users\\<username>\\AppData\\Local\\easy
    local_app_data = os.getenv('LOCALAPPDATA')
    if local_app_data:
        data_dir = pathlib.Path(local_app_data) / _appname
    else:
        data_dir = pathlib.Path.home() / 'AppData' / 'Local' / _appname
    data_dir.mkdir(parents=True, exist_ok=True)
    return str(data_dir)


## App config (this code is likely to be moved elsewhere, otherwise module should be renamed)
## Duplicated code to avoid premature abstractions


# TODO take a create= param 
def get_system_appconfig_path() -> str: 
    """
    TODO
    """
    if os.name == 'posix':
        return _get_posix_appconfig_path()
    elif os.name == 'nt':
        return _get_win_appconfig_path()
    else:
        raise NotImplementedError('unknown system')


def _get_posix_appconfig_path() -> str:
    xdg_config_home = os.getenv('XDG_CONFIG_HOME')
    if xdg_config_home:
        config_dir = pathlib.Path(xdg_config_home) / _appname
    else:
        config_dir = pathlib.Path.home() / '.config' / _appname
    config_dir.mkdir(parents=True, exist_ok=True)
    return str(config_dir)


def _get_win_appconfig_path() -> str:
    program_data = os.getenv('PROGRAMDATA')
    if program_data:
        data_dir = pathlib.Path(program_data) / _appname
    else:
        data_dir = pathlib.Path.home() / 'AppData' / 'Local' / _appname
    data_dir.mkdir(parents=True, exist_ok=True)
    return str(data_dir)