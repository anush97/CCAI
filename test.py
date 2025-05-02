from google.protobuf.json_format import MessageToDict
import json

# Dump the entire response to dict
response_dict = MessageToDict(response._pb)

# Pretty print it
print(json.dumps(response_dict, indent=2))
