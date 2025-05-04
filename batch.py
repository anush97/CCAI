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

# Split into batches of 20
batch_size = 20
batches = [questions[i:i+batch_size] for i in range(0, len(questions), batch_size)]
print(f"📦 Split into {len(batches)} batches of up to {batch_size} questions each.")

# Store results from all batches
all_results = []

for batch_num, batch_questions in enumerate(batches, start=1):
    print(f"\n🚀 Starting Batch {batch_num} with {len(batch_questions)} questions")

    # Create a new conversation
    conversation_client = dialogflow.ConversationsClient()
    conversation = conversation_client.create_conversation(
        parent=parent,
        conversation=dialogflow.Conversation(
            conversation_profile=conversation_profile_path,
            lifecycle_state=dialogflow.Conversation.LifecycleState.IN_PROGRESS,
        )
    )
    conversation_name = conversation.name
    print(f"🧠 Conversation {batch_num} created: {conversation_name}")

    # Create participant
    participants_client = dialogflow.ParticipantsClient()
    participant = participants_client.create_participant(
        parent=conversation_name,
        participant=dialogflow.Participant(role=dialogflow.Participant.Role.END_USER),
    )
    participant_name = participant.name
    print(f"👤 Participant created: {participant_name}")

    # Process questions in the current batch
    for i, question in enumerate(batch_questions):
        print(f"\n🔹 Q{(batch_num-1)*batch_size + i + 1}: {question}")

        # Send question
        request = dialogflow.AnalyzeContentRequest(
            participant=participant_name,
            text_input=dialogflow.TextInput(text=question, language_code="en-US")
        )
        response = participants_client.analyze_content(request=request)
        time.sleep(1)

        # Parse response
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

            all_results.append({
                "batch": batch_num,
                "question": question,
                "answer": answer,
                "source_titles": "; ".join(source_titles),
                "source_uris": "; ".join(source_uris)
            })

            print(f"✅ Answer: {answer}")
        except Exception as e:
            print(f"❌ Could not extract answer: {e}")
            all_results.append({
                "batch": batch_num,
                "question": question,
                "answer": "No answer or suggestion available",
                "source_titles": "",
                "source_uris": ""
            })

# Save to CSV
df = pd.DataFrame(all_results)
df.to_csv("agent_assist_batched_responses.csv", index=False)
print("\n✅ All responses saved to agent_assist_batched_responses.csv")
