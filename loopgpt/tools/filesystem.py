from loopgpt.tools.base_tool import BaseTool
import os


class ReadFromFile(BaseTool):
    @property
    def args(self):
        return {"file": "Path to the file to read as a string."}

    @property
    def resp(self):
        return {
            "content": "Contents of the file. If the file doesn't exist, this field will be empty."
        }

    def run(self, file):
        try:
            with open(file, "r") as f:
                return {"content": f.read()}
        except Exception:
            return {"content": ""}


class WriteToFile(BaseTool):
    @property
    def args(self):
        return {
            "file": "Path of the file to write to as a string.",
            "content": "Content to be written to the file as a string.",
        }

    @property
    def resp(self):
        return {"success": "true or false"}

    def run(self, file, content):
        with open(file, "w") as f:
            f.write(content)
        return {"success": True}


class AppendToFile(BaseTool):
    @property
    def desc(self):
        return "Appends content to the end of a file."

    @property
    def args(self):
        return {
            "file": "Path of the file to append to as a string.",
            "content": "The content to be appended to the file as a string.",
        }

    @property
    def resp(self):
        return {"success": "true or false"}

    def run(self, file, content):
        with open(file, "a") as f:
            f.write(content)
        return {"success": True}


class DeleteFile(BaseTool):
    @property
    def args(self):
        return {"file": "Path to the file to be deleted as a string."}

    @property
    def resp(self):
        return {"success": "true if the file was successfully deleted. Else false."}

    def run(self, file):
        try:
            os.remove(file)
            return {"success": True}
        except Exception:
            return {"success": False}


class CheckIfFileExists(BaseTool):
    @property
    def args(self):
        return {"file": "Path to the check if file exists as a string."}

    @property
    def resp(self):
        return {"exists": "true if the file exists, else false."}

    def run(self, file):
        return {"exists": os.path.isfile(file)}


class ListFiles(BaseTool):
    @property
    def args(self):
        return {
            "path": "Path to the directory to list files and directories in as a string. This is a required argument.",
            "recursive": "If true, list files and directories recursively. Else, list only the files and directories in the given path. This is a required argument.",
            "show_hidden": "If true, show hidden files and directories. Defaults to False.",
            "exclude_dirs": "If true, exclude directories from the result. Defaults to False.",
        }

    @property
    def resp(self):
        return {
            "result": "list of files and directories",
        }

    @property
    def desc(self):
        return "List files and directories in a given path. Directories end with a trailing slash."

    def run(self, path, recursive, show_hidden=False, exclude_dirs=False):
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
        return {"result": entries_list}


class GetCWD(BaseTool):
    @property
    def args(self):
        return {}

    @property
    def resp(self):
        return {"path": "Path to the current working directory"}

    @property
    def desc(self):
        return "Find the current working directory using this command"

    def run(self):
        try:
            cwd = os.getcwd()
            return {"path": cwd}
        except Exception as e:
            return (
                f"An error occurred while getting the current working directory: {e}."
            )


class MakeDirectory(BaseTool):
    @property
    def args(self):
        return {"path": "Path of the directory to be made"}

    @property
    def resp(self):
        return {"success": "True if the directory was created, False otherwise."}

    @property
    def desc(self):
        return "Make a new directory at the given path"

    def run(self, path):
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
