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

# Dialogflow setup
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

# Process questions
output_rows = []

for i, question in enumerate(questions):
    print(f"\n🔹 Q{i+1}/{len(questions)}: {question}")

    # Step 1: Send the question
    analyze_request = dialogflow.AnalyzeContentRequest(
        participant=participant_name,
        text_input=dialogflow.TextInput(text=question, language_code="en-US")
    )
    response = participants_client.analyze_content(request=analyze_request)

    # Step 2: Extract message name from response
    response_dict = MessageToDict(response._pb)
    try:
        message_name = response_dict["message"]["name"]
        print(f"📝 Message ID: {message_name}")
    except Exception as e:
        print(f"❌ Could not extract message name: {e}")
        output_rows.append({
            "question": question,
            "answer": "No message ID found",
            "source_title": "",
            "source_uri": ""
        })
        continue

    # Step 3: Wait and request article suggestion
    time.sleep(2.5)
    request = dialogflow.SuggestArticlesRequest()
    request.participant = participant_name
    request.latest_message = message_name

    try:
        suggestion = participants_client.suggest_articles(request=request)

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
    except Exception as e:
        output_rows.append({
            "question": question,
            "answer": f"Error fetching suggestion: {str(e)}",
            "source_title": "",
            "source_uri": ""
        })
        print(f"❌ Error during suggestion: {e}")

# Save results
df = pd.DataFrame(output_rows)
df.to_csv("agent_assist_responses.csv", index=False)
print("\n✅ All responses saved to agent_assist_responses.csv")
