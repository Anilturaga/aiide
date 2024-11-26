class Num:
    """
    Defines an integer field for a JSON schema.

    Attributes:
        name (str): The name of the field.
        description (str, optional): A description of the field.
        enums (list, optional): A list of allowed values for the field.
    """

    def __init__(
        self, name: str, description: str | None = None, enums: list | None = None
    ):
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


class Float:
    """
    Defines a float field for a JSON schema.

    Attributes:
        name (str): The name of the field.
        description (str, optional): A description of the field.
        enums (list, optional): A list of allowed values for the field.
    """

    def __init__(
        self, name: str, description: str | None = None, enums: list | None = None
    ):
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


class Str:
    """
    Defines a string field for a JSON schema.

    Attributes:
        name (str): The name of the field.
        description (str, optional): A description of the field.
        enums (list, optional): A list of allowed values for the field.
    """

    def __init__(
        self, name: str, description: str | None = None, enums: list | None = None
    ):
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


class Bool:
    """
    Defines a boolean field for a JSON schema.

    Attributes:
        name (str): The name of the field.
        description (str, optional): A description of the field.
        enums (list, optional): A list of allowed values for the field.
    """

    def __init__(
        self, name: str, description: str | None = None, enums: list | None = None
    ):
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


class Object:
    """
    Defines a dictionary field for a JSON schema.

    Attributes:
        name (str): The name of the field.
        description (str, optional): A description of the field.
        properties (list, optional): A list of objects representing the properties of the dictionary.
        enums (list, optional): A list of allowed values for the field.
    """

    def __init__(
        self,
        name: str,
        description: str | None = None,
        properties: list = [],
        enums: list | None = None,
        required: list[str] | None = None,
    ):
        self.name = name
        self.description = description
        self.properties = properties
        self.enums = enums
        self.required = required

    def json(self):
        """
        Returns a dictionary representing the JSON schema for this dictionary field.

        Returns:
            dict: The JSON schema for this dictionary field.
        """
        schema: dict = {"type": "object"}
        if self.description:
            schema["description"] = self.description
        if self.properties:
            schema["properties"] = {
                prop.name: next(iter(prop.json().values())) for prop in self.properties
            }
        if self.enums:
            schema["enum"] = self.enums
        if self.required:
            schema["required"] = self.required
        schema["additionalProperties"] = False
        return {self.name: schema}


class Array:
    """
    Defines a list field for a JSON schema.

    Attributes:
        name (str): The name of the field.
        description (str, optional): A description of the field.
        item (object, optional): An object representing the type of items in the list.
        enums (list, optional): A list of allowed values for the field.
    """

    def __init__(
        self,
        name: str,
        description: str | None = None,
        item: Str | Num | Float | Bool | Object | None = None,
        enums: list | None = None,
    ):
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


class AnyOf:
    """
    Defines an anyOf field for a JSON schema.

    Attributes:
        name (str): The name of the field.
        description (str, optional): A description of the field.
        options (list): A list of objects representing the possible types.
    """

    def __init__(self, name: str, options: list):
        self.name = name
        self.options = options

    def json(self):
        """
        Returns a dictionary representing the JSON schema for this anyOf field.

        Returns:
            dict: The JSON schema for this anyOf field.
        """
        schema = {
            "anyOf": [next(iter(option.json().values())) for option in self.options]
        }
        return {self.name: schema}

class Nullable:
    """
    Makes the direct child of this object nullable

    Attributes:
        child (object): The object to make nullable
    """

    def __init__(self, child: Str | Num | Float | Bool | Object | Array):
        self.child = child
    def json(self):
        schema = self.child.json()
        schema[self.child.name]["type"] = [schema[self.child.name]["type"], "null"] 
        return schema

def tool_def_gen(
    name: str,
    description: str | None = None,
    properties: list = [],
    required: list | None = None,
):
    """
    Defines the JSON schema for an OpenAI function call definition.

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


def structured_outputs_gen(
    name: str, properties: list = [], required: list[str] | None = []
):
    """
    Defines the JSON Schema for the OpenAI structured outputs definition.

    Args:
        name (str): The name of the structured output.
        properties (list, optional): A list of property definitions. Defaults to an empty list.
        required (list[str] | None, optional): A list of required properties. Defaults to an empty list.

    Returns:
        dict: The generated schema for the structured output.
    """
    schema = {
        "name": name,
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {k: v for d in properties for k, v in d.json().items()},
            "required": required,
            "additionalProperties": False,
        },
    }
    return schema
