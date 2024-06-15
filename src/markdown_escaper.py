def escape_dot(string_to_convert):
    converted_string = str()
    chars_to_escape = ['.', '-', '!', '>', '(', ')']
    for char in string_to_convert:
        if char in chars_to_escape:
            converted_string += f'\{char}'
        else:
            converted_string += char
    return converted_string
