from loopgpt.tools.base_tool import BaseTool
import os


class ReadFromFile(BaseTool):
    """Reads the contents of a file.

    Args:
        file (str): Path to the file to read.

    Returns:
        str: Contents of the file.
    """

    def run(self, file: str):
        try:
            with open(file, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return f"Error: Could not read file {file}."


class WriteToFile(BaseTool):
    """Write content to a file. This will overwrite the file if it already exists.

    Args:
        file (str): Path of the file to write to.
        content (str): Content to be written to the file.

    Returns:
        bool: True if the file was successfully written to. Else False.
    """

    def run(self, file: str, content: str):
        try:
            with open(file, "w") as f:
                f.write(content)
            return True
        except:
            return False


class AppendToFile(BaseTool):
    """Appends content to the end of a file. Creates the file if it does not exist.

    Args:
        file (str): Path of the file to append to.
        content (str): Content to be appended to the file.

    Returns:
        bool: True if the file was successfully appended to. Else False.
    """

    def run(self, file: str, content: str):
        with open(file, "a") as f:
            f.write(content)
        return True


class DeleteFile(BaseTool):
    """Deletes a file.

    Args:
        file (str): Path to the file to be deleted.

    Returns:
        bool: True if the file was successfully deleted. Else False.
    """

    def run(self, file: str):
        try:
            os.remove(file)
            return True
        except Exception:
            return False


class CheckIfFileExists(BaseTool):
    """Checks if a file exists.

    Args:
        file (str): Path to the file to check.

    Returns:
        bool: True if the file exists. Else False.
    """

    def run(self, file: str):
        return os.path.isfile(file)


class ListFiles(BaseTool):
    """List files and directories in a given path. Directories end with a trailing slash.

    Args:
        path (str): Path to the directory to list files and directories in.
        recursive (bool): If true, list files and directories recursively. Else, list only the files and directories in the given path.
        show_hidden (bool): If true, show hidden files and directories. Defaults to False.
        exclude_dirs (bool): If true, exclude directories from the result. Defaults to False.

    Returns:
        List[str]: List of files and directories.
    """

    def run(
        self,
        path: str,
        recursive: bool,
        show_hidden: bool = False,
        exclude_dirs: bool = False,
    ):
        entries_list = []
        with os.scandir(path) as entries:
            for entry in entries:
                if show_hidden or not entry.name.startswith("."):
                    if entry.is_dir():
                        if not exclude_dirs:
                            entries_list.append(f"{entry.name}/")
                        if recursive:
                            entries_list.extend(
                                self.run(
                                    os.path.join(path, entry.name),
                                    recursive,
                                    show_hidden,
                                    exclude_dirs,
                                )["result"]
                            )
                    else:
                        entries_list.append(entry.name)
        return entries_list


class GetCWD(BaseTool):
    """Get the current working directory.

    Returns:
        str: Path to the current working directory.
    """

    def run(self):
        try:
            cwd = os.getcwd()
            return {"path": cwd}
        except Exception as e:
            return (
                f"An error occurred while getting the current working directory: {e}."
            )


class MakeDirectory(BaseTool):
    """Create a new directory at the given path.

    Args:
        path (str): Path of the directory to be made.

    Returns:
        bool: True if the directory was created, False otherwise.
    """

    def run(self, path: str):
        try:
            os.makedirs(path)
            return {"success": True}
        except Exception as e:
            return f"An error occurred while creating a new directory path: {e}."


FileSystemTools = [
    WriteToFile,
    ReadFromFile,
    AppendToFile,
    DeleteFile,
    CheckIfFileExists,
    ListFiles,
    GetCWD,
    MakeDirectory,
]
