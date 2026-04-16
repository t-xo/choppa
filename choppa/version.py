import regex as re
from typing import Optional, Union, BinaryIO, TextIO
import io

class SrxVersion:
    VERSION_1_0 = "1.0"
    VERSION_2_0 = "2.0"

    HEADER_BUFFER_LENGTH = 1024
    VERSION_PATTERN = re.compile(r'<srx[^>]+version="([^"]+)"')

    @classmethod
    def parse_string(cls, version_string: str) -> str:
        if version_string == cls.VERSION_1_0:
            return cls.VERSION_1_0
        elif version_string == cls.VERSION_2_0:
            return cls.VERSION_2_0
        else:
            raise ValueError(f"Unrecognized SRX version: {version_string}.")

    @classmethod
    def detect(cls, reader: Union[TextIO, BinaryIO]) -> str:
        """
        Detects SRX version from a reader.
        Does not consume the reader (if seekable).
        """
        try:
            current_pos = reader.tell()
            header_data = reader.read(cls.HEADER_BUFFER_LENGTH)
            if hasattr(header_data, "decode"):
                header = header_data.decode("utf-8", errors="ignore")
            else:
                header = header_data
            
            reader.seek(current_pos)
            
            matcher = cls.VERSION_PATTERN.search(header)
            if matcher:
                return cls.parse_string(matcher.group(1))
            
            raise ValueError("SRX version not found in document header.")
        except Exception as e:
            if isinstance(e, ValueError):
                raise e
            raise ValueError(f"Error detecting SRX version: {e}")
