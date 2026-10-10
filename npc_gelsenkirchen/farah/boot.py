# Подключение MPFB2 к bpy-модулю как обычного аддона (без менеджера расширений).
import sys, os, bpy, addon_utils
HERE = os.path.dirname(os.path.abspath(__file__))
_ud = os.path.join(HERE, "mpfb_user"); os.makedirs(_ud, exist_ok=True)
bpy.utils.extension_path_user = lambda *a, **k: _ud
addons = bpy.utils.user_resource('SCRIPTS', path="addons", create=True)
link = os.path.join(addons, "mpfb")
if not os.path.exists(link):
    os.symlink(os.path.join(HERE, "mpfb2", "src", "mpfb"), link)
if addons not in sys.path:
    sys.path.insert(0, addons)
def enable():
    mod = addon_utils.enable("mpfb", default_set=True, handle_error=lambda e: print("enable err", repr(e)))
    return mod
