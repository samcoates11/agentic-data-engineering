# Minimal smoke test for the Bedrock Converse API, with no tool config -
# confirms model access works before layering tool-calling on top in agent.py.
import boto3

REGION = "eu-west-2"
# Requires this model to be enabled under Bedrock > Model access for REGION,
# otherwise the call below raises a ValidationException ("Access ... is not allowed").
MODEL_ID = "amazon.nova-micro-v1:0"

def main():
    client = boto3.client(
        "bedrock-runtime",
        region_name=REGION,
    )

    response = client.converse(
        modelId=MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": "Explain a data pipeline in one sentence."
                    }
                ],
            }
        ],
    )

    print("\nBedrock response:")
    # Converse returns a single "message" (not "messages") containing content blocks.
    answer = response["output"]["message"]["content"][0]["text"]

    print(answer)

if __name__ == "__main__":
    main()