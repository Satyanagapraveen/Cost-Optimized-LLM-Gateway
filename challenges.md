## Challenge 1

### Indentation error in inline Python script

**Error logs when I tried to run it**

```text
File "<string>", line 6
	content, model, latency, cost, usage = await execute_llm_call(
	^
IndentationError: expected an indented block after function definition on line 5
```

**Problem**

The body of `async def test():` was not indented. Python requires every statement inside a function to be indented consistently, so the script stopped before it ever called `execute_llm_call`.

**Fix**

Indent the lines inside the function body and keep the call formatted like a normal Python block.

## Challenge 2

### Groq model name did not exist

**Error logs when I tried to run it**

```text
litellm.exceptions.NotFoundError: litellm.NotFoundError: GroqException - {"error":{"message":"The model `qwen-3.8-27b` does not exist or you do not have access to it.","type":"invalid_request_error","code":"model_not_found"}}
```

**Problem**

The test script used `groq/qwen-3.8-27b`, but the workspace configuration defined the working low-tier model as `groq/qwen/qwen3.8-27b` in `config.yaml`. LiteLLM sent the wrong model path to Groq, so the provider returned a 404-style model-not-found error.

**Fix**

Read the model name from configuration instead of hardcoding it in the test:

```python
from app.config import config

model_name = config.yaml.models.low_tier
```

That change made the smoke test succeed and returned `verified` from the configured Groq model.
