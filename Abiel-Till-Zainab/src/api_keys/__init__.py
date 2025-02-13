from groq import Groq
from pydantic import SecretStr

with open('api_keys/groq.txt', 'r') as f:
    groq_api_key = SecretStr(f.read().strip())

with open('api_keys/jina.txt', 'r') as f:
    jina_api_key = SecretStr(f.read().strip())

def print_available_groq_models():
	client = Groq(
		api_key=groq_api_key.get_secret_value(),
	)
	models = client.models.list()

	for model in models.data:
		print(model.id)