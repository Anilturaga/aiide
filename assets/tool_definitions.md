# AIIDE's tool use tutorial

Defining OpenAI function definitions in python currently has two ways
1. JSON schema
2. Pydantic classes

**JSON SCHEMA**<br/>
Defining schemas in python is very verbose and has no intellisense.
for example:
```json
{
    "type": "function",
    "function": {
        "name": "add_or_modify_form_values",
        "parameters": {
            "type": "object",
            "properties": {
                "field_name": {"type": "string"},
                "value": {"type": "string"},
            },
        },
        "description": "tool to add or modify field values",
    },
    "required":["field_name","value"]
}
```

**Pydantic**<br/>
Since Pydantic is meant mostly for defining and validating types, the class based structure makes it just as verbose. It gets more challenging when defining nested structures since each level requires a new class


**Our solution**<br/>
aiide has the following types defined
```python
from aiide.tools import TOOL_DEF, INT, FLOAT, STR, BOOL, LIST, DICT
```

Here is the implementation of the above tool definition with `aiide.tools`<br/>
The above tool has two input attributes
1. We start with defining the function name and it's description
```python
TOOL_DEF(
    name = "add_or_modify_form_values",
    description = "tool to add or modify field values",
```
2. Next we start with defining the properties where both attributes are strings<br/>STR itself has name and description as arguments

```python
TOOL_DEF(
    name = "add_or_modify_form_values",
    description = "tool to add or modify field values",
    properties = [
        STR(
            name = "field_name",
            enums=self.parent.df["Field"].values.tolist()
            ),
        STR(
            name = "value"
        )
    ]
)
```
**Complex example**
1. Let's say we want to update the tool definition to enable adding/updating multiple records at a time. Here is the json definition where the LLM calls the tool with an array of dictionaries with field and value as the keys.
```python
{
    "type": "function",
    "function": {
        "name": "add_or_modify",
        "description": "tool to add or modify field values",
        "parameters": {
            "type": "object",
            "properties": {
                "add_or_update": {
                    "type": "array",
                    "description": "Add values for one or more placeholders at a time",
                    "items": {
                        "type": "object",
                        "name":"nest",
                        "properties": {
                            "field": {
                                "type": "string",
                                "description": "Field name you are adding or modifying a value",
                            },
                            "value": {
                                "type": "string",
                                "description": "Value of the field",
                            },
                        },
                    },
                }
            },
            "required": ["add_or_update"],
        },
    },
}
```
2. Here is a step by step conversion
```python
TOOL_DEF(
    name = "add_or_modify",
    description = "tool to add or modify field values",
```

Now let's define the properties which takes in a list of tool objects. Here we only have one object which itself is a LIST(I know, confusing but it's true)
```python
TOOL_DEF(
    name = "add_or_modify",
    description = "tool to add or modify field values",
    properties=[LIST(name="add_or_update",description="Add values for one or more placeholders at a time")]
```

The LIST also takes an item argument which can be any tool object. In our case it's a DICT with two keys
```python
TOOL_DEF(
    name="add_or_modify",
    description="tool to add or modify field values",
    properties=[
        LIST(
            name="add_or_update",
            description="Add values for one or more placeholders at a time",
            item=DICT(
                name="nest",
                properties=[
                    STR(
                        name="field",
                        description="Field name you are adding or modifying a value",
                    ),
                    STR(name="value", description="Value of the field"),
                ],
            ),
        )
    ],
)
```