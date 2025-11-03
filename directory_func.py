from pathlib import Path


default_location = "server_location"

def path_directory() -> Path:
    base_path = Path(__file__).resolve().parent / default_location
    return base_path


def list_directory(base_directory: Path, recursive: bool = False)-> list[Path]:
    base_path = Path(base_directory)

    file_list = []

    # rglob represents all files recursively while glob is not recursive
    iterator = base_path.rglob('*') if recursive else base_path.glob('*')

    # potential features show files size and modification date
    # doesn't show any directory info
    for file_path_obj in iterator:
        if file_path_obj.is_file():
            relative_path = file_path_obj.relative_to(base_path)
            file_list.append(relative_path)

    return file_list

def str_path(path_list: list[Path]) -> str:
    pretty_path = ""
    for path in path_list:
        pretty_path += str(path) + "\n"

    return pretty_path


if __name__ == "__main__":
    home = path_directory()
    print(str_path(list_directory(home, True)))
