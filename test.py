from google.protobuf.json_format import MessageToDict
import json

# Send a test question and inspect the full structure
response = participants_client.analyze_content(
    request=dialogflow.AnalyzeContentRequest(
        participant=participant_name,
        text_input=dialogflow.TextInput(text=questions[0], language_code="en-US")
    )
)

# Convert full response to dictionary
response_dict = MessageToDict(response._pb)
print(json.dumps(response_dict, indent=2))