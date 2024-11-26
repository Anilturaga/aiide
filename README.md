<div align="center"><picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://github.com/Anilturaga/aiide/blob/main/assets/figures/logo_dark.svg?raw=True">
  <img alt="aiide" src="https://github.com/Anilturaga/aiide/blob/main/assets/figures/logo.svg?raw=True" width=200">
</picture></div>
<br/>

aiide is a framework to build LLM copilots.

It is born out of 3 years of experience building LLM applications starting from GPT-3 completion models to the latest frontier chat models.

| What you get with aiide? | What's not part of aiide? |
|--------------------------|--------------------------|
| Full control over content sent to the LLM | Verbose abstractions for common prompting techniques |
| Tools and structured outputs are first class citizens for actions and content generation | Chains as a core building block |
| Simplified streaming by default to build real-time apps | Output parsing tools |
| Messages history is a Pandas DataFrame | Complex nested JSON objects |


## Table of Contents
* [Installation](#installation)
* [Chat](#chat)
* [Memory](#memory)
* [Structured Outputs](#structured-outputs)
* [Tools](#tools)
* [JSON Schema](#json-schema)
* [Usage Costs](#usage-costs)
* [/llms.txt Specification](#llms-txt-specification)
* [Misc](#misc)

## Installation
Let's start by installing the package.
```bash
pip install aiide
```
This also installs LiteLLM and Pandas by default. If you would like to use other LLM providers such as Anthropic or Google AI, please install the respective SDK as well.

The whole tutorial uses OpenAI models but it should work with all the popular LLM providers.

## Chat
Now that aiide is installed, let's create a simple chatbot similar to ChatGPT free tier.

```python
from aiide import Aiide

class Chatbot(Aiide):
	def  __init__(self):
		self.setup(system_message="You are a helpful assistant.", model="gpt-4o-mini-2024-07-18")

agent = Chatbot()
while True:
    user_input = input("\nSend a message: ")
    if user_input == "exit":
        break
    for delta in agent.chat(user_message=user_input):
        if delta["type"] == "text":
            print(delta["delta"],end="")
	
```

Let's break down the code:
- We defined a class Chatbot that inherits from Aiide. Classes are a great way to encapsulate the chatbot logic and state. It also enables sharing state with tools and structured outputs as we will see later.
- We set up the chatbot with a system message and a model. The model can be anything supported by LiteLLM.
- We then create an instance of the Chatbot and start a loop to chat with the bot.
- The chat loop returns a generator of deltas. Each delta has a type and content. The type can be either text, tool_call or tool_response. If the delta type is text, it will have delta and content as it's keys. If the delta type is tool_call, it will have name and arguments as it's keys. If the delta type is tool_response, it will have name, arguments and response as it's keys.


> `setup` and `chat` has a lot of optional parameters that you can find while hovering over the method in your IDE. Some notable parameters for `setup` are `model`, `temperature`, `api_key`, and any supported LiteLLM completion parameters. Similarly, `chat` has parameters such as `tools`, `stop_words`, `tool_choice` etc.

#### User Message Input
`user_message` can take a couple of types of inputs. It can be a string as you've just seen, it can be an image object(`PIL.Image`) it can be an array of strings and images.

Different ways to use user_message:
```python
user_message = "What's the weather like in SF"
image = Image.open("image.jpg")
user_message = image
user_message = [image, "Annotate the attached image"]
```
<!--
user_message = {"RAG":"Some large content","query":"Actual user message"}
Reasoning for using dict as input:
When you pass a dict for user_message in aiide, it will only pass in the values to the LLM. The keys are instead useful to later update or remove pieces of information from the memory/chat history.
-->

## Memory

A natural question for the above snippet is how do we track the chat history?

aiide has first-class support for memory. I found that handling OpenAI JSON based schema is cumbersome and error-prone. So, I had abstracted the chat history into a Pandas DataFrame.

`messages` is a pandas DataFrame that stores all the messages, tool calls and responses of a chat session. 

You can access the memory of the chatbot by calling `agent.messages` in the above example.

The schema of the messages DataFrame is as follows:

| role | content | arguments | response |
|-------------|-----------|-------------| ------------ |
| system  | You are a helpful assistant | None | None |
| user  | What's the weather like in SF | None | None |
| tool  | {'name':'get_weather','id':'abc'} | {'location':'SF'} | {'temperature':'72'} |
| assistant  | The weather is 72 degress right now. | None | None |

You can use the memory DataFrame to analyze and manipulate the chat history and the tool calls and responses.

## Structured Outputs

Currently the LLM can respond with text in any format. Sometimes it thinks first, sometimes it will answer in code right away. What if we want to structure the output in a specific way?

Currently to my knowledge, OpenAI and Google AI supports structured outputs. aiide has a common interface for structured outputs.

Let's see how we can use structured outputs in aiide.

```python
from aiide import Aiide
from aiide.schema import structured_outputs_gen, Str

class Chatbot(Aiide):
    def  __init__(self):
        self.setup(system_message="You are a helpful assistant.", model="gpt-4o-mini-2024-07-18")
    def structured_ouputs(self):
        return structured_outputs_gen(
            name="chain_of_thought",
            properties=[
                Str(name="thinking", description="Use this field to think out loud. Breakdown the user's query, plan your response, etc."),
                Str(name="response"),
            ],
            required=["thinking", "response"],
        )

agent = Chatbot()
while True:
    user_input = input("\nSend a message: ")
    if user_input == "exit":
        break
    for delta in agent.chat(user_message=user_input,json_mode=True):
        if delta["type"] == "text":
            print(delta["delta"],end="")
```
Test out the infamous question `How many R letters are there in the word "strawberry"?`

Now, let's break down the changes code:
- We import `structured_outputs_gen` and `Str` from `aiide.schema`. Both of these will aide(heh) in defining the structured outputs json schema.
> I did not love pydantic for defining json schemas. I have observed that a lot of developers are omitting fields such as descriptions and enums while defining schemas with pydantic. It also does not have an easier way to dynamically change the schema. So, I have created a simple interface to define structured outputs that is as flexible as possible and also helps the developer understand what they can do for each type by the help of intellisense. Please checkout the [aiide's JSON Schema](./assets/schema_definitions.md) for more information.
- We override a method `structured_outputs` in `Aiide` that returns the structured output generator. The beauty of this is that you can define multiple structured outputs return the appropriate one based on the context.
- We pass `json_mode=True` to the `chat` method. This will enable the structured outputs.


## Tools

Tools are the heart of aiide. They are the actions that the LLM can take. They can be as simple as a function call or as complex as a hierarchical LLM agents.

You define tools as classes and pass instances to the Aiide instance. The lifecycle of handling the tool calls, it's execution and feeding the response back into the LLM is all handled by aiide. You however, can still control the execution of the tool based on the values of deltas.

Let's see how we can define a tool in aiide.

```python
import random
import json
from aiide import Aiide, Tool
from aiide.schema import tool_def_gen, Str

class WeatherTool(Tool):
    def __init__(self, parent):
        self.error = False

    def tool_def(self):
        return tool_def_gen(
            name="get_current_weather",
            description="Get the current weather in a given location",
            properties=[
                Str(
                    name="location",
                    description="The city and state, e.g. San Francisco, CA",
                ),
                Str(name="unit", enums=["celsius", "fahrenheit"]),
            ],
        )


    def main(self, location, unit="default"): # type: ignore
        if self.error:
            return json.dumps({"error": 404})
        else:
            return json.dumps({"location": location, "temperature": random.randint(0, 100), "unit": unit})

class Agent(Aiide):
    def __init__(self):
        # passing the chatbot instance to the tool for bi-directional communication
        self.weatherTool = WeatherTool(self)
        self.setup(
            system_message="You are a helpful assistant.",
        )

agent = Agent()
for delta in agent.chat(
    user_message="What's the weather like in San Francisco, Tokyo, and Paris?",
    tools=[agent.weatherTool],
):
    # printing response based on the type of delta
    if delta["type"] == "text":
        print(delta["delta"], end="")
    if delta["type"] == "tool_call":
        print("Tool called:", delta["name"], "with arguments:", delta["arguments"])
    if delta["type"] == "tool_response":
        print("Tool response for tool:", delta["name"], " with arguments:", delta["arguments"], "is:", delta["response"])

    # changing the execution of the tool based on the context of the conversation
    if delta["type"] == "tool_call" and "tokyo" in delta["arguments"].lower():
        agent.weatherTool.error = True
    else:
        agent.weatherTool.error = False


```

Let's break down the code:
- We import `Tool` from `aiide` and `tool_def_gen` and `Str` from `aiide.schema`. `Tool` is the base class for all tools in aiide. `tool_def_gen` is a tool definition generator that helps in defining the tool schema. `Str` is a string type that can have description, enums.
- We define a class `WeatherTool` that inherits from `Tool`. We define the `__init__` method to initialize the tool. We define the `tool_def` method to define the tool schema. We finally define the `main` method to define the tool logic.
- For activating the tool, we can pass the tool instance to the `chat` method through the `tools` array parameter. 
- As mentioned previously, the delta has three types: `text`, `tool_call`, and `tool_response`. When type of delta is tool, the delta will have name and arguments keys for the tool called. After the tool is executed, the delta will have a type of tool_response and the response key will have the response of the tool.
- If you observe the code, we are setting a boolean flag `error` in the tool instance based on the location. This way, you can control the execution of a tool based on the context of the conversation and the tool's state. A good example would be taking user's consent before executing code.
- This way, you can activate or deactivate tools based on the context of the conversation.

#### Delta Schema

The delta schema is as follows:

| Type           | Keys                                                                                   |
|----------------|----------------------------------------------------------------------------------------|
| text           | - delta: The text content of the delta                                                |
|                | - content: The full content of the delta, including the text and any additional data   |
| tool_call      | - name: The name of the tool being called                                              |
|                | - arguments: The arguments passed to the tool                                          |
| tool_response  | - name: The name of the tool that generated the response                               |
|                | - arguments: The arguments passed to the tool                                          |
|                | - response: The response generated by the tool                                         |

## JSON Schema

As mentioned earlier, aiide has a simple interface to define JSON schemas. This is useful for defining structured outputs and tools that might change based on the context of the conversation.

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

There is currently one disadvantage to using aiide's schema definitions which is the lack of validation of the generated schema. Right now, we are trusting the API provider to provide the correct schema but we will be adding that feature in the future.

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

If you are relatively new to JSON Schema, you might not have come across AnyOf and Nullable. Here is a quick explanation:
1. AnyOf: This is used when you want to define multiple types for a single attribute. For example, if you want to define a field that can be either a string or a number, you can use AnyOf
2. Nullable: This is used when you want to define a field that can be null. For example, if you want to define a field that can be either a string or null, you can use Nullable. This is very useful for structured outputs cause currently all the fields are required.

## Usage Costs
Tracking tokens and API costs can be a pain. aiide has a simple interface to track the tokens and the costs of the API calls.

```python
from aiide import Aiide

class Chatbot(Aiide):
	def  __init__(self):
		self.setup(system_message="You are a helpful assistant.", model="gpt-4o-mini")

agent = Chatbot()
while True:
    user_input = input("\nSend a message: ")
    if user_input == "exit":
        break
    for delta in agent.chat(user_message=user_input):
        if delta["type"] == "text":
            print(delta["delta"],end="")
    print("Usage",agent.usage)
```
agent.usage will return a dictionary with the following keys:
```markdown
| Name              | Description                                      |
|-------------------|--------------------------------------------------|
| prompt_tokens     | Number of tokens in the prompt                   |
| completion_tokens | Number of tokens in the completion               |
| usd               | Cost of the API call in USD                      |
```
It works with Images, Tools and Structured Outputs.

## llms-txt-specification
Since all of the documentation is in the README of the aiide repository, you can pass this file to an LLM as context to help you write aiide copilots with ease.

Here is an example of how it works:
[Link to Gist](https://gist.github.com/Anilturaga/763a23abe102cfc4856e1c11cbef672e)

## Misc

### Acknowledgements
aiide has taken inspiration and code from the following repositories:
- Guidance
- LiteLLM
- Partialjson
- OpenAI SDK