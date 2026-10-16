import hyperparams as hp

def get_item[T](id: int, items: list[T]) -> T | None:
    for item in items:
        if item.id == id: return item # type: ignore

    return None

def debug(s: str):
    if hp.DEBUG:
        print(s)