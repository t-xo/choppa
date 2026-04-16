import io
from typing import Optional


class TextManager:

    def __init__(
        self,
        text: Optional[str] = None,
        reader: Optional[io.TextIOBase] = None,
        buffer_length: Optional[int] = None,
    ) -> None:

        """
        Creates text manager containing given text. Reading more text is not
        possible when using this constructor.
        Takes either text or reader (not both)
        @param text
        @param reader
        @param buffer_length read buffer size
        """

        self.next_character: str = ""
        self.buffer_length: int = 0
        self.reader: Optional[io.TextIOBase] = None
        self.text_initialized: bool = False

        self.text: str = ""

        assert (text is None) != (reader is None), "You have to provide either text or reader"

        if text is not None:
            self.text = text
            self.text_initialized = True
            self.reader = None
            self.buffer_length = len(text)

        if reader is not None:
            self.reader = reader
            assert buffer_length is not None and buffer_length > 0, "You have to provide buffer length for the reader"
            self.buffer_length = buffer_length

    def get_text(self) -> str:
        """
        @return current text
        """
        self.init_text()
        return self.text

    def has_more_text(self) -> bool:
        """
        @return true if more text can be read
        """
        self.init_text()
        return self.next_character != ""

    def read_text(self, amount: int) -> None:
        """
        Deletes given amount of characters from current character buffer and
        tries to read up to given amount of new characters and stores them in
        current character buffer.
        @param amount amount of characters to read
        @throws AssertionError if self.has_more_text returns False or amount is greater than buffer size
        """
        self.init_text()

        assert amount > 0, "Amount must be positive."
        assert amount <= self.buffer_length, "Amount to read is larger than buffer size."
        assert self.has_more_text(), "No more text to read."

        self.text = (
            self.text[amount:]
            +
            self.next_character
            + self.read(amount)
        )

    def init_text(self) -> None:
        """
        Reads initial text from reader if it has not been initialized yet.
        """
        if not self.text_initialized:
            self.text_initialized = True
            self.text = self.read(self.buffer_length + 1)

    def read(self, amount: int) -> str:
        """
        Reads the given amount of characters and returns them as a string.
        Updates next_character by reading one additional character.
        @param amount amount to be read
        @return read characters as a string
        """

        assert self.reader is not None

        result: str = self.reader.read(amount)
        count: int = len(result)

        if count == amount:
            self.next_character = result[-1]
            result = result[:-1]
        elif count > 0 and count < amount:
            self.next_character = ""
        else:
            result = ""
            self.next_character = ""

        return result




