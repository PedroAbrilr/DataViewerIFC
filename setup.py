import shutil
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py


class BuildPy(_build_py):
    def run(self):
        copies = [
            ("docs/manual_usuario.md", "src/dataviewerifc/data/manual_usuario.md"),
            ("Modelfile",              "src/dataviewerifc/data/Modelfile"),
        ]
        for src, dst in copies:
            s = Path(src)
            if s.exists():
                shutil.copy(s, dst)
        super().run()


setup(cmdclass={"build_py": BuildPy})
