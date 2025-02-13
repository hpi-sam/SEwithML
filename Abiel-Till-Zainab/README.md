# Unit Test Generator

An agentic tool for generating high-quality unit tests for Python code.

## Features

- Generate unit tests using language models
- Iterativly generate readable test cases that avoid common test smells and target test coverage
- Use the model's semantic understanding of the code to specifically target edge cases, which:
  - Improves test coverage and bug discovery rate
  - Reduces the number of tests (and thus inference and maintenance costs) using RAG-based similarity checking
  - We include postprocessing to uniformly format the tests using isort and black
- Run it in a Streamlit UI with langchain graph execution logging

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/hpi-sam/SEwithML.git
cd Abiel-Till-Zainab

# Create and activate a virtual environment (optional but recommended)
python -m venv test_generator
source test_generator/bin/activate  # On Windows: test_generator\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### Environment Setup

> [!IMPORTANT]
> Input your OpenAI API key in the `.env` file to run the tool. Other model providers are optional and have to be manually configured. Also at least Python 3.8 is required.

The tool requires API keys for the language- and embedding models. Set up a `.env` file in the project's root:

```bash
echo "OPENAI_API_KEY=your-openai-key" > .env
```

Add your API keys to the `.env` file:
```
OPENAI_API_KEY=your-openai-key (required)
GROQ_API_KEY=your-groq-key (optional)
JINA_API_KEY=your-jina-key (optional)
```

> [!NOTE]
> Get your API keys from:
> - OpenAI API key: [https://platform.openai.com/api-keys](https://platform.openai.com/)
> - Groq API key: [https://api.groq.com/](https://console.groq.com)
> - Jina API key: [https://cloud.jina.ai/](https://jina.ai)

## Usage

### Run the Streamlit App

```bash
# From the project root directory:
streamlit run src/app.py
```

Here you can input your code and generate unit tests. It also lets you load previous runs and continue working on them.
Try it out! 🧪
