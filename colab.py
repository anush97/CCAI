
from google.cloud import dialogflow_v2beta1 as dialogflow
from google.protobuf.json_format import MessageToDict
import json
import time

# Set project + profile info
project_id = "prj-sandbox-ccaas-lab-0"
location = "global"
conversation_profile_id = "3gEEJo2VQlmrGX1jme06FQ"
conversation_profile_path = f"projects/{project_id}/locations/{location}/conversationProfiles/{conversation_profile_id}"
parent = f"projects/{project_id}/locations/{location}"

# Create conversation
conversation_client = dialogflow.ConversationsClient()
conversation = conversation_client.create_conversation(
    parent=parent,
    conversation=dialogflow.Conversation(
        conversation_profile=conversation_profile_path,
        lifecycle_state=dialogflow.Conversation.LifecycleState.IN_PROGRESS,
    )
)
conversation_name = conversation.name
print("🧠 Conversation created:", conversation_name)

# Create participant
participants_client = dialogflow.ParticipantsClient()
participant = participants_client.create_participant(
    parent=conversation_name,
    participant=dialogflow.Participant(role=dialogflow.Participant.Role.END_USER),
)
participant_name = participant.name
print("👤 Participant created:", participant_name)

# Test question
question = "What is a premium?"

# Send the question
request = dialogflow.AnalyzeContentRequest(
    participant=participant_name,
    text_input=dialogflow.TextInput(text=question, language_code="en-US")
)
response = participants_client.analyze_content(request=request)

# Print raw Protobuf response
print("\n🧾 Raw Protobuf response:")
print(response)

# Print parsed dictionary
print("\n🧾 Parsed Dictionary:")
response_dict = MessageToDict(response._pb)
print(json.dumps(response_dict, indent=2))
