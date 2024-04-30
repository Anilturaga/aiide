import inspect
def find_inner_classes(cls, base_class=None):
    inner_classes = []
    # print("base class", base_class)
    for name, obj in inspect.getmembers(cls):
        if inspect.isclass(obj) and obj.__module__ == cls.__module__:
            # Check if the class is defined inside the given class (not imported)
            if hasattr(obj, "__qualname__") and obj.__qualname__.startswith(
                cls.__qualname__ + "."
            ):
                if base_class is None or issubclass(obj, base_class):
                    inner_classes.append({"class": obj, "type": "agent"})
                else:
                    inner_classes.append({"class": obj, "type": "tool"})

    return inner_classes
