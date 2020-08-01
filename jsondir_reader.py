import os
import json
import mmfbase

class Reader(mmfbase.Reader):

    def get_file(self, fn):
        return os.path.join(self.fp, fn)

    def get_project_file(self):
        with open(os.path.join(self.fp, "project.json"), "rb") as f:
            return json.loads(f.read())
