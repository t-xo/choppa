import regex as re

SRX_HORIZONTAL_WHITESPACE = r"[\x09\x20\u00A0\u1680\u180E\u2000-\u200A\u202F\u205F\u3000]"
SRX_VERTICAL_WHITESPACE = r"[\x0A\x0B\x0C\x0D\x85\u2028\u2029]"


def is_escaped(pattern: str, index: int) -> bool:
    backslash_count = 0
    cursor = index - 1
    while cursor >= 0 and pattern[cursor] == "\\":
        backslash_count += 1
        cursor -= 1
    return backslash_count % 2 == 1


def remove_block_quotes(pattern: str) -> str:
    """
    Replaces block quotes in regular expressions with normal quotes. For
    example "\\Qabc\\E" will be replace with "\\a\\b\\c".

    @param pattern
    @return pattern with replaced block quotes
    """

    pattern_builder: str = ""
    quote: bool = False
    previous_char: str = ""

    for current_char in pattern:
        if quote:
            if previous_char == "\\" and current_char == "E":
                quote = False
                pattern_builder = pattern_builder[:-2]
            else:
                pattern_builder += "\\" + current_char

        else:
            if previous_char == "\\" and current_char == "Q":
                quote = True
                pattern_builder = pattern_builder[:-1]
            else:
                pattern_builder += current_char
        previous_char = current_char

    return pattern_builder


def escape_block_quotes(pattern: str) -> str:
    """
    Replaces SRX ``\\Q ... \\E`` quoted text with Python-regex-safe literals.
    """

    pattern_builder = []
    quote_builder = []
    quote = False
    index = 0

    while index < len(pattern):
        current_char = pattern[index]
        next_char = pattern[index + 1] if index + 1 < len(pattern) else ""

        if current_char == "\\" and not is_escaped(pattern, index):
            if next_char == "Q" and not quote:
                quote = True
                index += 2
                continue
            if next_char == "E" and quote:
                pattern_builder.append(re.escape("".join(quote_builder)))
                quote_builder = []
                quote = False
                index += 2
                continue

        if quote:
            quote_builder.append(current_char)
        else:
            pattern_builder.append(current_char)

        index += 1

    if quote:
        pattern_builder.append(re.escape("".join(quote_builder)))

    return "".join(pattern_builder)


def normalize_srx_anchors(pattern: str) -> str:
    """
    Emulate SRX region anchoring for ``^``.
    """

    pattern_builder = []
    in_character_class = False

    for index, current_char in enumerate(pattern):
        escaped = is_escaped(pattern, index)

        if current_char == "[" and not escaped:
            in_character_class = True
        elif current_char == "]" and not escaped:
            in_character_class = False

        if (
            current_char == "^"
            and not escaped
            and not in_character_class
            and (index == 0 or pattern[index - 1] in "(|")
        ):
            pattern_builder.append(r"(?:\G|^)")
        else:
            pattern_builder.append(current_char)

    return "".join(pattern_builder)


def translate_srx_regex(pattern: str, normalize_anchors: bool = True) -> str:
    """
    Translate Okapi SRX regex escapes that Python's regex module does not
    parse the same way.
    """

    pattern = escape_block_quotes(pattern)
    if normalize_anchors:
        pattern = normalize_srx_anchors(pattern)

    pattern_builder = []
    index = 0
    while index < len(pattern):
        current_char = pattern[index]
        next_char = pattern[index + 1] if index + 1 < len(pattern) else ""

        if current_char == "\\" and not is_escaped(pattern, index):
            if next_char == "h":
                pattern_builder.append(SRX_HORIZONTAL_WHITESPACE)
                index += 2
                continue
            if next_char == "v":
                pattern_builder.append(SRX_VERTICAL_WHITESPACE)
                index += 2
                continue
            if next_char == "e":
                pattern_builder.append(r"\x1B")
                index += 2
                continue

        pattern_builder.append(current_char)
        index += 1

    return "".join(pattern_builder)


def finitize(pattern: str, infinity: int) -> str:
    """
    Changes unlimited length pattern to limited length pattern. It is done by
    replacing constructs with "*" and "+" symbols with their finite
    counterparts - "{0,n}" and {1,n}.
    As a side effect block quotes are replaced with normal quotes
    by using {@link #removeBlockQuotes(String)}.

    @param pattern pattern to be finitized
    @param infinity "n" number
    @return limited length pattern
    """

    pattern = remove_block_quotes(pattern)
    pattern_builder = []
    index = 0

    while index < len(pattern):
        current_char = pattern[index]

        if current_char == "{" and not is_escaped(pattern, index):
            parsed_range = _parse_open_range(pattern, index)
            if parsed_range is not None:
                end_index, minimum = parsed_range
                pattern_builder.append("{" + minimum + "," + str(infinity) + "}")
                index = end_index + 1
                continue

        if current_char == "*" and not is_escaped(pattern, index):
            pattern_builder.append("{0," + str(infinity) + "}")
        elif (
            current_char == "+"
            and not is_escaped(pattern, index)
            and not _plus_is_quantifier_suffix(pattern, index)
        ):
            pattern_builder.append("{1," + str(infinity) + "}")
        else:
            pattern_builder.append(current_char)

        index += 1

    return "".join(pattern_builder)


def _parse_open_range(pattern: str, start_index: int):
    index = start_index + 1
    while index < len(pattern) and pattern[index].isspace():
        index += 1

    digit_start = index
    while index < len(pattern) and pattern[index].isdigit():
        index += 1

    if digit_start == index:
        return None

    minimum = pattern[digit_start:index]

    while index < len(pattern) and pattern[index].isspace():
        index += 1

    if index >= len(pattern) or pattern[index] != ",":
        return None

    index += 1
    while index < len(pattern) and pattern[index].isspace():
        index += 1

    if index >= len(pattern) or pattern[index] != "}":
        return None

    return index, minimum


def _plus_is_quantifier_suffix(pattern: str, plus_index: int) -> bool:
    if plus_index == 0:
        return False

    previous_char = pattern[plus_index - 1]
    if previous_char in "?*+":
        return True

    if previous_char != "}":
        return False

    open_index = pattern.rfind("{", 0, plus_index)
    if open_index == -1 or is_escaped(pattern, open_index):
        return False

    body = pattern[open_index + 1 : plus_index - 1]
    return bool(re.fullmatch(r"[0-9],?[0-9]?", body))


def remove_capturing_groups(pattern: str) -> str:
    """
    Replaces capturing groups with non-capturing groups in the given regular
    expression. As a side effect block quotes are replaced with normal quotes
    by using {@link #removeBlockQuotes(String)}.

    @param pattern
    @return modified pattern
    """
    new_pattern = remove_block_quotes(pattern)
    pattern_builder = []
    in_character_class = False

    for index, current_char in enumerate(new_pattern):
        escaped = is_escaped(new_pattern, index)

        if current_char == "[" and not escaped:
            in_character_class = True
        elif current_char == "]" and not escaped:
            in_character_class = False

        if (
            current_char == "("
            and not escaped
            and not in_character_class
            and (index + 1 >= len(new_pattern) or new_pattern[index + 1] != "?")
        ):
            pattern_builder.append("(?:")
        else:
            pattern_builder.append(current_char)

    return "".join(pattern_builder)
