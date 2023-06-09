def chunk_by_delimiter(data, delimiter, chunk_size=2000):
    chunks = []
    curr_len = 0
    lines = data.split(delimiter)
    for line in lines:
        if chunks and curr_len + len(line) < chunk_size:
            chunks[-1] = delimiter.join([chunks[-1], line])
            curr_len += len(line)
        else:
            chunks.append(line)
            curr_len = len(line)
    return chunks


class ChunkedFileStream:
    def __init__(self, path):
        self.path = path
        with open(path, "r", encoding="utf-8") as f:
            data = f.read()
        self.chunk_size = 2000
        self.chunks = self.chunk(data)
        self.chunk_index = 0

    def read_chunk(self):
        if self.chunk_index >= len(self.chunks):
            return None
        chunk = self.chunks[self.chunk_index]
        self.chunk_index += 1
        return chunk

    def chunk(self, data):
        if self.path.endswith("txt"):
            return chunk_by_delimiter(data, "\n", self.chunk_size)
        elif self.path.endswith("tex"):
            return chunk_by_delimiter(data, "\n\n", self.chunk_size)
        raise NotImplementedError()


streams = {}


def read_chunk_from_file(path):
    if path not in streams:
        streams[path] = ChunkedFileStream(path)
    return streams[path].read_chunk()
