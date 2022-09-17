import traceback
import sys
# import the unpack module
from wowsunpack import WoWsUnpack

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: %s <path to WoWs folder>" % sys.argv[0])
        sys.exit(1)

    try:
        game_path = sys.argv[1]
        unpack = WoWsUnpack(game_path)
        unpack.reset()
        unpack.unpackGameParams()
        unpack.decodeGameParams()

        unpack.unpackGameMaps()
        unpack.decodeLanguages()

        unpack.unpackGameIcons()
        unpack.packAppAssets()
    except Exception as e:
        print("Error: %s" % e)
        traceback.print_exc()
        sys.exit(1)
