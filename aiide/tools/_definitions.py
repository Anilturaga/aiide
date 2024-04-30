class INT:
    """
    Defines an integer field for a JSON schema.

    Attributes:
        name (str): The name of the field.
        description (str, optional): A description of the field.
        enums (list, optional): A list of allowed values for the field.
    """
    def __init__(self, name, description=None, enums=None):
        self.name = name
        self.description = description
        self.enums = enums
    
    def json(self):
        """
        Returns a dictionary representing the JSON schema for this integer field.

        Returns:
            dict: The JSON schema for this integer field.
        """
        schema = {"type": "integer"}
        if self.description:
            schema["description"] = self.description
        if self.enums:
            schema["enum"] = self.enums
        return {self.name: schema}


class FLOAT:
    """
    Defines a float field for a JSON schema.

    Attributes:
        name (str): The name of the field.
        description (str, optional): A description of the field.
        enums (list, optional): A list of allowed values for the field.
    """
    def __init__(self, name, description=None, enums=None):
        self.name = name
        self.description = description
        self.enums = enums
    
    def json(self):
        """
        Returns a dictionary representing the JSON schema for this float field.

        Returns:
            dict: The JSON schema for this float field.
        """
        schema = {"type": "number"}
        if self.description:
            schema["description"] = self.description
        if self.enums:
            schema["enum"] = self.enums
        return {self.name: schema}


class STR:
    """
    Defines a string field for a JSON schema.

    Attributes:
        name (str): The name of the field.
        description (str, optional): A description of the field.
        enums (list, optional): A list of allowed values for the field.
    """
    def __init__(self, name, description=None, enums=None):
        self.name = name
        self.description = description
        self.enums = enums
    
    def json(self):
        """
        Returns a dictionary representing the JSON schema for this string field.

        Returns:
            dict: The JSON schema for this string field.
        """
        schema = {"type": "string"}
        if self.description:
            schema["description"] = self.description
        if self.enums:
            schema["enum"] = self.enums
        return {self.name: schema}


class BOOL:
    """
    Defines a boolean field for a JSON schema.

    Attributes:
        name (str): The name of the field.
        description (str, optional): A description of the field.
        enums (list, optional): A list of allowed values for the field.
    """
    def __init__(self, name, description=None, enums=None):
        self.name = name
        self.description = description
        self.enums = enums
    
    def json(self):
        """
        Returns a dictionary representing the JSON schema for this boolean field.

        Returns:
            dict: The JSON schema for this boolean field.
        """
        schema = {"type": "boolean"}
        if self.description:
            schema["description"] = self.description
        if self.enums:
            schema["enum"] = self.enums
        return {self.name: schema}


class LIST:
    """
    Defines a list field for a JSON schema.

    Attributes:
        name (str): The name of the field.
        description (str, optional): A description of the field.
        item (object, optional): An object representing the type of items in the list.
        enums (list, optional): A list of allowed values for the field.
    """
    def __init__(self, name, description=None, item=None, enums=None):
        self.name = name
        self.description = description
        self.items = item
        self.enums = enums
    
    def json(self):
        """
        Returns a dictionary representing the JSON schema for this list field.

        Returns:
            dict: The JSON schema for this list field.
        """
        schema = {"type": "array"}
        if self.description:
            schema["description"] = self.description
        if self.items:
            schema["items"] = next(iter(self.items.json().values()))
        if self.enums:
            schema["enum"] = self.enums
        return {self.name: schema}


class DICT:
    """
    Defines a dictionary field for a JSON schema.

    Attributes:
        name (str): The name of the field.
        description (str, optional): A description of the field.
        properties (list, optional): A list of objects representing the properties of the dictionary.
        enums (list, optional): A list of allowed values for the field.
    """
    def __init__(self, name, description=None, properties=[], enums=None):
        self.name = name
        self.description = description
        self.properties = properties
        self.enums = enums
    
    def json(self):
        """
        Returns a dictionary representing the JSON schema for this dictionary field.

        Returns:
            dict: The JSON schema for this dictionary field.
        """
        schema = {"type": "object"}
        if self.description:
            schema["description"] = self.description
        if self.properties:
            schema["properties"] = {prop.name: next(iter(prop.json().values())) for prop in self.properties}
        if self.enums:
            schema["enum"] = self.enums
        return {self.name: schema}


def TOOL_DEF(name, description=None, properties=[], required=None):
    """
    Defines the JSON schema for an OpenAI function call.

    Args:
        name (str): The name of the function.
        description (str, optional): A description of the function.
        properties (list, optional): A list of objects representing the properties of the function.
        required (list, optional): A list of required properties for the function.

    Returns:
        dict: The JSON schema for the OpenAI function call.
    """
    schema = {
        "type": "function",
        "function": {
            "name": name,
            "parameters": {
                "type": "object",
                "properties": {k: v for d in properties for k, v in d.json().items()},
            },
        },
    }
    if description:
        schema["function"]["description"] = description
    if required:
        schema["function"]["parameters"]["required"] = required
    return schema
