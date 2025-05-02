
# Step 3: Read questions from GCS
import gcsfs
import json

fs = gcsfs.GCSFileSystem()
bucket_path = 'gs://agent_assist_belair_on/non_ambiguous_questions.json'

with fs.open(bucket_path, 'r') as f:
    data = json.load(f)

questions = [item['question'] for item in data if 'question' in item]
print(f"✅ Loaded {len(questions)} questions.")

# Step 4: Dialogflow / Agent Assist setup
from google.cloud import dialogflow_v2beta1 as dialogflow
import pandas as pd
import time

project_id = "prj-sandbox-ccaas-lab-0"
location = "global"
conversation_profile_id = "3gEEJo2VQlmrGX1jme06FQ"
conversation_profile_path = f"projects/{project_id}/locations/{location}/conversationProfiles/{conversation_profile_id}"
parent = f"projects/{project_id}/locations/{location}"

# Step 5: Create a conversation
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

# Step 6: Create a participant (user)
participants_client = dialogflow.ParticipantsClient()
participant = participants_client.create_participant(
    parent=conversation_name,
    participant=dialogflow.Participant(role=dialogflow.Participant.Role.END_USER),
)
participant_name = participant.name
print("👤 Participant created:", participant_name)

# Step 7: Ask questions one-by-one and collect responses
output_rows = []

for i, question in enumerate(questions):
    print(f"\n🔹 Q{i+1}/{len(questions)}: {question}")

    # Send question
    request = dialogflow.AnalyzeContentRequest(
        participant=participant_name,
        text_input=dialogflow.TextInput(text=question, language_code="en-US")
    )
    participants_client.analyze_content(request=request)

    # Wait for agent response to be generated
    time.sleep(3.5)

    # Fetch all messages again
    messages = list(conversation_client.list_messages(parent=conversation_name))

    print("📥 Recent messages:")
    for msg in sorted(messages, key=lambda m: m.create_time, reverse=True):
        print(f"- Role: {msg.participant_role}, Content: {msg.content.strip()}")

    # Try to find the latest AI-generated response
    latest_reply = ""
    for msg in sorted(messages, key=lambda m: m.create_time, reverse=True):
        if msg.participant_role != "END_USER" and msg.content.strip():
            latest_reply = msg.content.strip()
            break

    output_rows.append({
        "question": question,
        "answer": latest_reply if latest_reply else "No reply"
    })

    print(f"✅ Answer: {latest_reply if latest_reply else 'No reply'}")
    print("-" * 60)

# Step 8: Save to CSV
df = pd.DataFrame(output_rows)
df.to_csv("agent_assist_responses.csv", index=False)
print("\n✅ All responses saved to agent_assist_responses.csv")
