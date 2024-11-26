# AIIDE's JSON Schema definitions

Since aiide uses LiteLLM under the hood, all the schema definitions follow OpenAI's specification.

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
Since Pydantic is meant mostly for defining and validating types, the class based structure makes it just as verbose. It gets more challenging when defining nested structures since each level requires a new class and also changing parts of the schema such as enums, required fields etc. on the fly is not as easy.


**Our solution**<br/>
aiide has the following types defined
```python
from aiide.schema import tool_def_gen, structured_outputs_gen, Num, Float, Str, Bool, Array, Object, AnyOf, Nullable
```

Here is the implementation of the above tool definition with `aiide.schema`<br/>
The above tool has two input attributes
1. We start with defining the function name and it's description
```python
tool_def_gen(
    name = "add_or_modify_form_values",
    description = "tool to add or modify field values",

```
2. Next we start with defining the properties where both attributes are strings<br/>Str itself has name and description as arguments

```python
tool_def_gen(
    name = "add_or_modify_form_values",
    description = "tool to add or modify field values",
    properties = [
        Str(
            name = "field_name",
            enums=self.parent.df["Field"].values.tolist()
            ),
        Str(
            name = "value"
        )
    ]
)
```

There are a couple of advantages to using aiide's schema definitions
1. You get intellisense for all the attributes
2. You can easily change the schema on the fly based on the tool's state and the chat context
3. Tool definition and tool execution logic stays in the same tool class and nesting definitions still ensures everything is in one place

There is **one** disadvantage to using aiide's schema definitions which is the lack of validation of the generated schema. Right now, we are trusting the API provider to provide the correct schema but we will be adding validation in the future.

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
tool_def_gen(
    name = "add_or_modify",
    description = "tool to add or modify field values",
```

Now let's define the properties which takes in a list of tool objects. Here we only have one object which itself is a Array(I know, confusing but it's true)
```python
tool_def_gen(
    name = "add_or_modify",
    description = "tool to add or modify field values",
    properties=[Array(name="add_or_update",description="Add values for one or more placeholders at a time")]
```

The Array also takes an item argument which can be any tool object. In our case it's a Object with two keys
```python
tool_def_gen(
    name="add_or_modify",
    description="tool to add or modify field values",
    properties=[
        Array(
            name="add_or_update",
            description="Add values for one or more placeholders at a time",
            item=Object(
                name="nest",
                properties=[
                    Str(
                        name="field",
                        description="Field name you are adding or modifying a value",
                    ),
                    Str(name="value", description="Value of the field"),
                ],
            ),
        )
    ],
)
```

If you are relatively new to JSON schema, you might not have come across AnyOf and Nullable. Here is a quick explanation:
1. AnyOf: This is used when you want to define multiple types for a single attribute. For example, if you want to define a field that can be either a string or a number, you can use AnyOf
2. Nullable: This is used when you want to define a field that can be null. For example, if you want to define a field that can be either a string or null, you can use Nullable. This is very useful for structured outputs cause currently all the fields are required.