# Step 1: Install dependencies
!pip install --upgrade gcsfs google-cloud-dialogflow google-auth

# Step 2: Import and auth
from google.colab import auth
auth.authenticate_user()

import gcsfs
import json

# Step 3: Load the file from GCS
fs = gcsfs.GCSFileSystem()
bucket_path = 'gs://agent_assist_belair_on/non_ambiguous_questions.json'

with fs.open(bucket_path, 'r') as f:
    data = json.load(f)

# Step 4: Extract questions
questions = [item['question'] for item in data if 'question' in item]
print(f"Loaded {len(questions)} questions.")

# Step 5: Set up Google Cloud Client for Agent Assist
from google.cloud import dialogflow_v2beta1 as dialogflow

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
print("Conversation created:", conversation_name)

# Create participant
participants_client = dialogflow.ParticipantsClient()
participant = participants_client.create_participant(
    parent=conversation_name,
    participant=dialogflow.Participant(role=dialogflow.Participant.Role.END_USER),
)
participant_name = participant.name
print("Participant created:", participant_name)

# Step 6: Send each question
responses = []
for question in questions:
    request = dialogflow.AnalyzeContentRequest(
        participant=participant_name,
        text_input=dialogflow.TextInput(text=question, language_code="en-US")
    )
    response = participants_client.analyze_content(request=request)

    # Collect basic text responses; can be extended to parse suggested replies, knowledge answers, etc.
    reply = response.reply_text if response.reply_text else "No reply"
    responses.append({
        'question': question,
        'answer': reply
    })
    print(f"Q: {question}\nA: {reply}\n")

# Optional: Convert to DataFrame for saving or export
import pandas as pd
df = pd.DataFrame(responses)
