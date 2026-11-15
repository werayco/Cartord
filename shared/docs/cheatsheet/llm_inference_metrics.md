# LLM inference metrics

Record four numbers for every Groq call. The source is the usage block on the finished message, including the streaming customer agent. The last streamed chunk carries the same block as a one-shot reply.

The calls are:

| Call | Where | How it returns |
| --- | --- | --- |
| Intent classifier | `classify_intent` | One response |
| Order slot model | `collect_order_details` | One response |
| Customer agent | `general_agent` | Streamed tokens, usage on the last chunk |
| Title generator | `generate_and_publish_title` | One response |

## Where the numbers come from

Read `response_metadata["token_usage"]` on the finished `AIMessage`:

- `queue_time`
- `prompt_time`
- `completion_time`
- `total_time`
- `completion_tokens`

`completion_tokens` already includes reasoning tokens. Use that count. The length of the visible reply is a character count, so it cannot feed these formulas.

Log one finished message before wiring the metrics and confirm those keys. LangChain sometimes nests the Groq usage differently between versions.

## Formulas

`N` is `completion_tokens`.

- **TTFT** = `queue_time + prompt_time`
- **TPOT** = `completion_time / (N - 1)`
- **Streaming TPS** = `(N - 1) / completion_time`
- **Effective TPS** = `N / total_time`

TTFT is the wait before generation starts. TPOT is the average time for each token after the first. Streaming TPS is the decode speed. Effective TPS spreads the same tokens over the whole call, so the wait for the first token pulls it down.

Skip TPOT and streaming TPS when `N` is under 2.

## Streaming agent

`general_agent` streams, and its usage still arrives once, on the last `AIMessage` chunk in the `messages` stream from `graph.astream`. Compute the four numbers there. Group chunks by `metadata["langgraph_node"]`, because one buyer message can run the classifier and then the agent.

Timestamps in `consumer.py` measure a different wait: the time from the start of `graph.astream` until the first non-empty `AIMessage.content`. That clock includes the graph and the path before Groq, so keep it as its own series, the buyer-facing time to the first token. Streaming TPS stays `(N - 1) / completion_time` from the usage block.

## One-shot calls

The classifier, the slot model, and the title model never emit token chunks, so there is no first or last token to stamp. Their TTFT, TPOT, and both TPS figures come only from the usage block on the finished message.

## Recording

Observe each value once per call with a Prometheus histogram on the existing `/api/v1/metrics` endpoint. Label it with the node and the model name. A conversation id would blow up the series.

Suggested series:

- `llm_ttft_seconds`
- `llm_tpot_seconds`
- `llm_streaming_tokens_per_second`
- `llm_effective_tokens_per_second`
- `llm_buyer_ttft_seconds` for the consumer clock on streamed replies