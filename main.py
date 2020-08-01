### CONFIG ###
# Replace "mmfpygame" with another filename (no extension) to select
# another rendering engine.
from mmfpygame import Game
# Replace "jsondir_reader" with another filename to select another
# file format
from jsondir_reader import Reader




#### CODE ####
import objects

if __name__ == "__main__":
    reader = Reader("test project")
    game = Game.from_dict(reader, reader.get_project_file())
    game.run()
