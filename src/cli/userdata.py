import os
import pathlib
import json
import base64
import collections.abc


class UnsafeJSONFileStore:

    # userdata are stored by address in a json file with format
    #
    # {
    #     "address1": "base64-encoded-value",
    #     "address2": "base64-encoded-value",
    #     ...
    # } 
    #
    # the 'base64-encoded-value' could represent anything.
    # In case it is a json-encoded object, 
    # the base64 value would be encoded as base64(json(obj)).
    # This class does not handle the inner encoding, that's up
    # to the caller.

    def __init__(self, path: str):
        # path represents the user data directory that MUST exists
        if not path:
            raise ValueError('invalid path')
        dir_path = pathlib.Path(path)
        if not dir_path.exists():
            raise ValueError(f"directory does not exist: {path}")
        if not dir_path.is_dir():
            raise ValueError(f"not a directory: {path}")
        file_path = dir_path / 'userdata.json'
        if not file_path.exists():
            try:
                with open(file_path, 'w') as f:
                    json.dump({}, f)
            except PermissionError:
                raise PermissionError(f"restricted access: {path}")
            except OSError as e:
                raise ValueError(f"cannot create userdata.json in {path}: {str(e)}")
        self._path = str(file_path)

    def store(self, addr: str, addr_data: str):
        v = base64.b64encode(addr_data.encode()).decode()
        with open(self._path, 'r') as f:
            data = json.load(f)
        data[addr] = v
        with open(self._path, 'w') as f:
            json.dump(data, f)

    def get(self, addr) -> str | None:
        with open(self._path, 'r') as f:
            data = json.load(f)
        return base64.b64decode(data[addr].encode()).decode() \
               if addr in data else None


# TODO define on a central location then inject it
_appname = 'easy'


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