# Tool-calling agent loop (not yet implemented).
#
# Planned shape, using the Bedrock Converse API demonstrated in bedrock_test.py:
#   1. Build a `toolConfig` describing each function in tools/data_tools.py
#      (name, description, JSON schema for its inputs).
#   2. Call `converse` with the conversation history and that `toolConfig`.
#   3. If the response contains a `toolUse` content block, look up and call
#      the matching Python function with the model-supplied arguments.
#   4. Append the function's return value to the conversation as a
#      `toolResult` message and call `converse` again.
#   5. Repeat until the response is plain text, then return it to the caller.
