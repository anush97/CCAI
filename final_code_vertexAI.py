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

# Config
project_id = "prj-sandbox-ccaas-lab-0"
location = "global"
conversation_profile_id = "3gEEJo2VQlmrGX1jme06FQ"
conversation_profile_path = f"projects/{project_id}/locations/{location}/conversationProfiles/{conversation_profile_id}"
parent = f"projects/{project_id}/locations/{location}"

# Split into batches of 10
batch_size = 10
batches = [questions[i:i + batch_size] for i in range(0, len(questions), batch_size)]
print(f"📦 Split into {len(batches)} batches of {batch_size} questions each.")

# Store all results
all_results = []

for batch_num, batch_questions in enumerate(batches, start=1):
    print(f"\n📦 ===== Starting Batch {batch_num} ({len(batch_questions)} questions) =====")
    time.sleep(5)

    print(f"⏳ Creating new conversation for Batch {batch_num}...")

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
    print(f"🧠 New Conversation created: {conversation_name}")

    # Create participant
    participants_client = dialogflow.ParticipantsClient()
    participant = participants_client.create_participant(
        parent=conversation_name,
        participant=dialogflow.Participant(role=dialogflow.Participant.Role.END_USER),
    )
    participant_name = participant.name
    print(f"👤 Participant created: {participant_name}")

    # Process each question in the batch
    for i, question in enumerate(batch_questions):
        global_q_index = (batch_num - 1) * batch_size + i + 1
        print(f"\n🔹 Asking Q{global_q_index}/{len(questions)}: {question}")
        print("⏳ Waiting for 10 seconds before sending...")
        time.sleep(10)

        # Send the question
        request = dialogflow.AnalyzeContentRequest(
            participant=participant_name,
            text_input=dialogflow.TextInput(text=question, language_code="en-US")
        )
        response = participants_client.analyze_content(request=request)

        # Parse the response
        response_dict = MessageToDict(response._pb)

        try:
            assist = (
                response_dict["humanAgentSuggestionResults"][0]
                .get("suggestKnowledgeAssistResponse", {})
                .get("knowledgeAssistAnswer", {})
            )

            suggestion = assist.get("suggestedQueryAnswer", {})
            answer_text = suggestion.get("answerText", "")
            sources = suggestion.get("generativeSource", {}).get("snippets", [])

            # Format sources for newline-separated strings
            source_titles = "\n".join([s.get("title", "") for s in sources])
            source_uris = "\n".join([s.get("uri", "") for s in sources])

            if answer_text:
                all_results.append({
                    "question": question,
                    "answer_status": "Answer + Sources",
                    "answer": answer_text,
                    "source_titles": source_titles,
                    "source_uris": source_uris,
                })
                print(f"✅ Answer: {answer_text}")

            elif sources:
                all_results.append({
                    "question": question,
                    "answer_status": "Sources Only",
                    "answer": "No answerText, but related documents found.",
                    "source_titles": source_titles,
                    "source_uris": source_uris,
                })
                print("⚠️ No answer, but sources found.")

            else:
                raise ValueError("No answerText or sources returned.")

        except Exception as e:
            print(f"❌ No response: {e}")
            all_results.append({
                "question": question,
                "answer_status": "No Response",
                "answer": "No response from Agent Assist.",
                "source_titles": "",
                "source_uris": ""
            })

# Save results
df = pd.DataFrame(all_results)

# Save to CSV
df.to_csv("agent_assist_responses.csv", index=False)

# Save to Excel
df.to_excel("agent_assist_responses.xlsx", index=False)

# Save to JSON
with open("agent_assist_responses.json", "w", encoding="utf-8") as f:
    json.dump(all_results, f, indent=2, ensure_ascii=False)

print("\n✅ Responses saved as:")
print("📄 CSV: agent_assist_responses.csv")
print("📘 Excel: agent_assist_responses.xlsx")
print("🧾 JSON: agent_assist_responses.json")
