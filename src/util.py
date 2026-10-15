"""Including utility functions for the project."""

from collections.abc import Callable


def split_map[T](text: str, mapper: Callable[[str], T] = lambda x: x, sep: str = '\t') -> list[T]:
    """Split the text by the separator and map each part with the mapper function.

    Unlike str.split(), this function will ignore empty parts."""
    return list(map(mapper, filter(None, text.split(sep))))


def join_map[T](items: list[T], mapper: Callable[[T], str] = str, sep: str = '\t') -> str:
    """Map each item with the mapper function and join the items with the separator."""
    mapped = list(map(mapper, items))
    for item in mapped:
        if sep in item:
            raise ValueError(f'An item contains the separator: {item}')
    return sep.join(mapped)


def bool_to_str(value: bool) -> str:
    """Convert a boolean value to a string representation.
    
    Unlike str(), this function returns a string that can be converted back to a boolean."""
    return '1' if value else ''  # Empty string is falsy.

def escape_tab(text: str) -> str:
    """Replace all tab characters in the text with a space."""
    return text.replace('\t', ' ')