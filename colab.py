import gcsfs
import json
import pandas as pd
import time
from google.cloud import dialogflow_v2beta1 as dialogflow
from google.protobuf.json_format import MessageToDict

# Load questions from GCS
fs = gcsfs.GCSFileSystem()
bucket_path = 'gs://agent_assist_belair_on/non_ambiguous_questions.json'

with fs.open(bucket_path, 'r') as f:
    data = json.load(f)

questions = [item['question'] for item in data if 'question' in item]
print(f"✅ Loaded {len(questions)} questions.")

# Setup
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

# Ask questions and collect answers
output_rows = []

for i, question in enumerate(questions):
    print(f"\n🔹 Q{i+1}/{len(questions)}: {question}")

    # Send question
    request = dialogflow.AnalyzeContentRequest(
        participant=participant_name,
        text_input=dialogflow.TextInput(text=question, language_code="en-US")
    )
    response = participants_client.analyze_content(request=request)
    time.sleep(1)

    # Parse full response
    response_dict = MessageToDict(response._pb)

    try:
        suggestion = (
            response_dict["humanAgentSuggestionResults"][0]
            ["suggestKnowledgeAssistResponse"]
            ["knowledgeAssistAnswer"]
            ["suggestedQueryAnswer"]
        )

        answer = suggestion.get("answerText", "No answer found")
        sources = suggestion.get("generativeSource", {}).get("snippets", [])

        source_titles = [s.get("title", "") for s in sources]
        source_uris = [s.get("uri", "") for s in sources]

        output_rows.append({
            "question": question,
            "answer": answer,
            "source_titles": "; ".join(source_titles),
            "source_uris": "; ".join(source_uris)
        })

        print(f"✅ Answer: {answer}")
    except Exception as e:
        print(f"❌ Could not extract answer: {e}")
        output_rows.append({
            "question": question,
            "answer": "No answer or suggestion available",
            "source_titles": "",
            "source_uris": ""
        })

# Save to CSV
df = pd.DataFrame(output_rows)
df.to_csv("agent_assist_responses.csv", index=False)
print("\n✅ All responses saved to agent_assist_responses.csv")
