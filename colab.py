

# Load questions from GCS
import gcsfs
import json

fs = gcsfs.GCSFileSystem()
bucket_path = 'gs://agent_assist_belair_on/non_ambiguous_questions.json'

with fs.open(bucket_path, 'r') as f:
    data = json.load(f)

questions = [item['question'] for item in data if 'question' in item]
print(f"✅ Loaded {len(questions)} questions.")

# Setup Dialogflow
from google.cloud import dialogflow_v2beta1 as dialogflow
import pandas as pd
import time

project_id = "prj-sandbox-ccaas-lab-0"
location = "global"
conversation_profile_id = "3gEEJo2VQlmrGX1jme06FQ"
conversation_profile_path = f"projects/{project_id}/locations/{location}/conversationProfiles/{conversation_profile_id}"
parent = f"projects/{project_id}/locations/{location}"

# Create a conversation
conversation_client = dialogflow.ConversationsClient()
conversation = conversation_client.create_conversation(
    parent=parent,
    conversation=dialogflow.Conversation(
        conversation_profile=conversation_profile_path,
        lifecycle_state=dialogflow.Conversation.LifecycleState.IN_PROGRESS,
    )
)
conversation_name = conversation.name

# Create participant
participants_client = dialogflow.ParticipantsClient()
participant = participants_client.create_participant(
    parent=conversation_name,
    participant=dialogflow.Participant(role=dialogflow.Participant.Role.END_USER),
)
participant_name = participant.name

# Ask questions and collect responses
output_rows = []

for i, question in enumerate(questions):
    print(f"\n🔹 Q{i+1}/{len(questions)}: {question}")

    # Send user message
    request = dialogflow.AnalyzeContentRequest(
        participant=participant_name,
        text_input=dialogflow.TextInput(text=question, language_code="en-US")
    )
    response = participants_client.analyze_content(request=request)

    # Get user message ID directly from response
    try:
        user_message_name = response.reply_text_message.name
    except Exception as e:
        print(f"❌ Could not get message ID: {e}")
        output_rows.append({
            "question": question,
            "answer": "No message ID found",
            "source_title": "",
            "source_uri": ""
        })
        continue

    # Wait for suggestion generation
    time.sleep(3)

    # Suggest article
    suggestion = participants_client.suggest_articles(
        participant=participant_name,
        latest_message=user_message_name
    )

    if suggestion.article_answers:
        top = suggestion.article_answers[0]
        output_rows.append({
            "question": question,
            "answer": top.snippet,
            "source_title": top.title,
            "source_uri": top.uri
        })
        print(f"✅ Answer: {top.snippet} | Source: {top.title}")
    else:
        output_rows.append({
            "question": question,
            "answer": "No article suggestion",
            "source_title": "",
            "source_uri": ""
        })
        print("⚠️ No article suggestion.")

# Save to CSV
df = pd.DataFrame(output_rows)
df.to_csv("agent_assist_responses.csv", index=False)
print("\n✅ All responses saved to agent_assist_responses.csv")
