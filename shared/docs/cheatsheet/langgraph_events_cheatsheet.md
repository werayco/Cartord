# LangChain and LangGraph Events Cheatsheet

This guide covers `graph.astream_events(inputs, config=config, version="v2")`, as used by the AI service graph test.

## 1. Event types

Standard names follow `on_<component>_<start|stream|end>`. Not every component or execution emits streaming events.

| Component | Events | Meaning |
| --- | --- | --- |
| Chat model | `on_chat_model_start`, `on_chat_model_stream`, `on_chat_model_end` | Starts a model call, emits message chunks, returns the completed response |
| Text completion LLM | `on_llm_start`, `on_llm_stream`, `on_llm_end` | Starts a completion, emits text chunks, finishes |
| Chain, graph, or node | `on_chain_start`, `on_chain_stream`, `on_chain_end` | Starts a workflow component, emits output updates, finishes |
| Tool | `on_tool_start`, `on_tool_end` | Starts a tool and returns its result |
| Retriever | `on_retriever_start`, `on_retriever_end` | Starts document retrieval and returns documents |
| Prompt | `on_prompt_start`, `on_prompt_end` | Starts prompt formatting and returns the formatted prompt |
| Custom | `on_custom_event` | Emits application-defined data, such as progress; supported in v2 |

A message chunk is not necessarily one token. It may contain text, tool-call data, or other content. A chain chunk may contain a complete node update rather than incremental model text.

## 2. Event fields

| Field | Purpose |
| --- | --- |
| `event` | What happened, such as `on_chain_end` |
| `name` | Component name, such as `agent`, `tools_condition`, or `LangGraph` |
| `data` | Input, chunk, output, or custom payload |
| `run_id` | Identifier for this component execution |
| `parent_ids` | Ancestor run IDs in v2, ordered from root to immediate parent |
| `tags` | Tags associated with the execution |
| `metadata` | Additional execution context |

Typical standard payload locations:

```python
event["data"]["input"]   # Start input; shape depends on component
event["data"]["chunk"]   # Stream update
event["data"]["output"]  # Completed output
```

These keys are not present in every event. For example, chat model start data uses `messages`. Check the event type before accessing its payload.

## 3. What happened in the AI service test

The observed run included:

```text
on_chain_start   LangGraph
on_chain_start   agent
on_chain_start   tools_condition
on_chain_end     tools_condition  -> __end__
on_chain_stream  agent           -> completed AIMessage
on_chain_end     agent           -> completed AIMessage
on_chain_stream  LangGraph       -> agent update
on_chain_end     LangGraph       -> final state
```

The graph generated a reply, and `tools_condition` returned `__end__`. No `on_chat_model_stream` events appeared in the captured output. Therefore, filtering exclusively for that event printed nothing even though the graph completed successfully.

The trace does not establish why model events were absent. Inspect the agent node, model initialization, and model invocation/configuration before deciding on a streaming fix.

## 4. Print the completed agent response

Use this loop inside the test's async `main()`, after defining `graph`, `inputs`, and `config`:

```python
async for event in graph.astream_events(
    inputs,
    config=config,
    version="v2",
):
    if (
        event["event"] == "on_chain_end"
        and event.get("name") == "agent"
    ):
        output = event["data"].get("output") or {}
        for message in output.get("messages", []):
            if message.content:
                print(message.content, flush=True)
```

This matches the observed agent output: a dictionary containing a `messages` list. It prints completed agent responses, not incremental tokens. If the agent runs multiple times in a tool loop, it handles each completed agent execution.

## 5. Print model text chunks when available

```python
async for event in graph.astream_events(
    inputs,
    config=config,
    version="v2",
):
    if event["event"] == "on_chat_model_stream":
        chunk = event["data"].get("chunk")
        content = getattr(chunk, "content", None)
        if isinstance(content, str) and content:
            print(content, end="", flush=True)

print()
```

This example handles string content. Models returning structured content blocks need block-specific text extraction. It intentionally does not print tool-call arguments or reasoning metadata.

## 6. Inspect event names without dumping state

```python
async for event in graph.astream_events(
    inputs,
    config=config,
    version="v2",
):
    print(
        event["event"],
        event.get("name"),
        "data_keys=", list(event.get("data", {})),
        flush=True,
    )
```

Prefer this diagnostic to printing the entire event: the graph input and final state can contain `access_token` and user information.

## 7. Run the script

Ensure the streaming loop is inside `main()` and the file ends with:

```python
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

Inside the AI service container, run:

```bash
python -m tests.test_graph
```

This executes the module. It does not automatically discover and run test functions like pytest does.

## Reference

See the official [LangChain astream_events reference](https://reference.langchain.com/python/langchain-core/runnables/base/Runnable/astream_events) for the v2 event schema, payload examples, and custom events. This guide specifically uses `version="v2"`; other protocol versions may differ.
