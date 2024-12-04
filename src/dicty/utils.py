import os


def get_path_relative_to_script(path: str) -> str:
    return os.path.join(os.path.dirname(__file__), path)
