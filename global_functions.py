import sys

if sys.platform.startswith("win"):
    import winreg

    def load_perflib_names():
        path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Perflib\CurrentLanguage"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
            data, _ = winreg.QueryValueEx(key, "Counter")
            # Decode REG_MULTI_SZ-like data
            if isinstance(data, bytes):
                data = data.decode("utf-16le", errors="ignore")
            items = [x for x in (data if isinstance(data, list) else data.split("\x00")) if x.strip()]
            names = {int(items[i]): items[i + 1] for i in range(0, len(items) - 1, 2)}
        return names

    def get_counter_from_id(id: int):
        names = load_perflib_names()
        return names.get(id, f"Unknown Counter ID {id}")

else:
    # Linux stub: just return dummy values
    def load_perflib_names():
        return {}

    def get_counter_from_id(id: int):
        return f"Counter ID {id} not available on Linux"