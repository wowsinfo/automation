import traceback
import sys

# import the unpack module
from wowsunpack import WoWsUnpack

# TODO: make this method public from wowsunpack
import os, shutil


def _resetDir(dirname: str):
    """
    Removes a directory if it exists and creates a new one.
    """
    if os.path.exists(dirname):
        shutil.rmtree(dirname)
    os.makedirs(dirname)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: %s <path to WoWs folder>" % sys.argv[0])
        sys.exit(1)

    try:
        game_path = sys.argv[1]
        unpack = WoWsUnpack(game_path)
        unpack.reset()
        _resetDir("scripts")

        unpack.unpackGameParams()
        unpack.decodeGameParams()

        unpack.unpackGameMaps()
        unpack.decodeLanguages()

        unpack.unpackGameIcons()
        unpack.unpack("scripts/*")
        unpack.packAppAssets()

        # compress app folder
        print("Compressing app folder...")
        os.system(r"..\pngquant\pngquant.exe .\app\assets\*\*.png --ext .png --force")
    except Exception as e:
        print("Error: %s" % e)
        traceback.print_exc()
        sys.exit(1)
