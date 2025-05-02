# Step 1: Install necessary libraries
!pip install --upgrade gcsfs google-cloud-dialogflow google-auth

# Step 2: Authenticate to GCP
from google.colab import auth
auth.authenticate_user()

# Step 3: Read questions from GCS
import gcsfs
import json

bucket_path = 'gs://agent_assist_belair_on/non_ambiguous_questions.json'
fs = gcsfs.GCSFileSystem()

with fs.open(bucket_path, 'r') as f:
    data = json.load(f)

# Step 4: Extract questions
questions = [item['question'] for item in data if 'question' in item]
print(f"Loaded {len(questions)} questions.")

# Step 5: Import Agent Assist client
from google.cloud import dialogflow_v2beta1 as dialogflow

project_id = "prj-sandbox-ccaas-lab-0"
location = "global"
conversation_profile_id = "3gEEJo2VQlmrGX1jme06FQ"

conversation_profile_path = f"projects/{project_id}/locations/{location}/conversationProfiles/{conversation_profile_id}"
parent = f"projects/{project_id}/locations/{location}"

# Step 6: Create a conversation
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

# Step 7: Create a participant (the customer)
participants_client = dialogflow.ParticipantsClient()
participant = participants_client.create_participant(
    parent=conversation_name,
    participant=dialogflow.Participant(role=dialogflow.Participant.Role.END_USER),
)
participant_name = participant.name
print("Participant created:", participant_name)

# Step 8: Send questions and store responses
import pandas as pd

output_rows = []

for question in questions:
    request = dialogflow.AnalyzeContentRequest(
        participant=participant_name,
        text_input=dialogflow.TextInput(text=question, language_code="en-US")
    )
    response = participants_client.analyze_content(request=request)

    # Try to extract article suggestion (Generative Knowledge Assist)
    if response.article_suggestion_results:
        for suggestion in response.article_suggestion_results:
            output_rows.append({
                'question': question,
                'answer': suggestion.article.snippet,
                'source_title': suggestion.article.title,
                'source_link': suggestion.article.uri
            })
    else:
        # If no article suggestion, fallback to reply_text or messages
        fallback_answer = ""
        if response.reply_text:
            fallback_answer = response.reply_text
        elif response.response_messages:
            texts = []
            for msg in response.response_messages:
                if msg.text and msg.text.text:
                    texts.extend(msg.text.text)
            fallback_answer = " ".join(texts)
        else:
            fallback_answer = "No reply"

        output_rows.append({
            'question': question,
            'answer': fallback_answer,
            'source_title': '',
            'source_link': ''
        })

# Step 9: Save to CSV
df = pd.DataFrame(output_rows)
df.to_csv("agent_assist_responses.csv", index=False)
print("✅ All responses saved to agent_assist_responses.csv")
