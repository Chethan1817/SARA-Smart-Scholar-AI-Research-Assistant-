import os
import json
import logging
from typing import List
from autogen import AssistantAgent, UserProxyAgent
import PyPDF2
import chromadb
from chromadb.utils import embedding_functions
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Configure logging
logging.basicConfig(level=logging.INFO)

# Set API key
api_key = "Set API key"
os.environ['OPENAI_API_KEY'] = api_key

# Initialize ChromaDB client
chroma_client = chromadb.Client()
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=api_key,
    model_name="text-embedding-ada-002"
)

# Function to get PDF file paths from a folder
def get_pdf_filepaths(folder_name: str) -> List[str]:
    try:
        folder_path = os.path.abspath(folder_name)
        pdf_files = [os.path.join(folder_path, file) for file in os.listdir(folder_path) if file.endswith('.pdf')]
        return pdf_files
    except Exception as e:
        logging.error(f"Error in getting PDF file paths: {e}")
        return []

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path: str) -> str:
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {e}")
        return ""

# Function to split text into chunks
def split_text(text: str) -> List[str]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    return text_splitter.split_text(text)

# Function to store text chunks in ChromaDB
def store_in_chromadb(chunks: List[str], collection_name: str):
    collection = chroma_client.create_collection(name=collection_name, embedding_function=openai_ef)
    for i, chunk in enumerate(chunks):
        collection.add(
            documents=[chunk],
            metadatas=[{"source": "pdf"}],
            ids=[f"id{i}"]
        )

# Function to query ChromaDB
def query_chromadb(query: str, collection_name: str, n_results: int = 5) -> str:
    collection = chroma_client.get_collection(name=collection_name, embedding_function=openai_ef)
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    return " ".join(results['documents'][0])

# Define the questions
questions = [
    "Who are the authors?",
    "What is the title of the page?",
    "What is the link to the page?",
    "How many mentions are relevant to keyword?",
    "What is the name of the pollutant shipwreck(s)?",
    "What are the coordinates of the sites?",
    "What is the type of pollution (oil, chemicals, UXO, corrosion)?",
    "Which World War period does it belong to (WWI, WWII, Unknown)?",
    "What is the date of publishing of the article?",
    "Are there mentions of sinking dates?",
    "Are coordinate locations mentioned (Yes or No)?"
]

# Configure the AI model
config_list = [
    {
        "model": "gpt-4",
        "api_key": api_key
    }
]

# Create the assistant agent
assistant = AssistantAgent(
    name="pdf_researcher",
    llm_config={
        "config_list": config_list,
    },
    system_message="""You are an expert in extracting and analyzing data from PDF documents, 
    focusing on historical and environmental research. Your task is to extract specific 
    information from the given PDF content and provide answers in JSON format."""
)

# Create the user proxy agent
user_proxy = UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=1,
    is_termination_msg=lambda x: isinstance(x, dict),
)

def analyze_pdf_content(collection_name: str) -> str:
    # Construct the task message
    task_msg = f"""Given the following PDF content from ChromaDB collection '{collection_name}', 
    extract answers to the following questions:
    {chr(10).join(questions)}
    Your final answer MUST be in JSON format with the questions as keys."""

    # Query ChromaDB for relevant content
    relevant_content = query_chromadb(task_msg, collection_name)

    # Start the conversation
    chat_result = user_proxy.initiate_chat(
        assistant,
        message=f"{task_msg}\n\nRelevant content:\n{relevant_content}"
    )

    # Extract the summary from the ChatResult object
    summary = chat_result.summary
    if isinstance(summary, str):
        try:
            json_response = json.loads(summary)
            return json.dumps(json_response, indent=2)
        except json.JSONDecodeError:
            logging.error(f"Failed to parse JSON from the summary: {summary}")
    else:
        logging.error(f"Unexpected summary type: {type(summary)}")
    
    return None

def get_answers(pdf_file: str, keywords: str) -> str:
    try:
        pdf_folder_path = f'pdf/{keywords.replace(" ", "_")}'
        all_pdfs = get_pdf_filepaths(pdf_folder_path)
        final_pdf = next((pdf for pdf in all_pdfs if pdf_file in pdf), None)

        if final_pdf is None:
            logging.error(f'PDF file not found. Searched in: {pdf_folder_path}')
            return None
        
        pdf_content = extract_text_from_pdf(final_pdf)
        if not pdf_content:
            logging.error("Failed to extract content from PDF.")
            return None

        # Split content into chunks and store in ChromaDB
        chunks = split_text(pdf_content)
        collection_name = f"pdf_{pdf_file.replace('.pdf', '')}"
        store_in_chromadb(chunks, collection_name)

        result = analyze_pdf_content(collection_name)
        
        if not result:
            logging.error("No result was returned or an error occurred during the process.")
            return None
        
        return result
    
    except Exception as e:
        logging.error(f"Error in get_answers function: {e}", exc_info=True)
        return None

# Example usage
if __name__ == "__main__":
    pdf_file = "brij5800-multiwreck-a4-report-web-0419-update.pdf"
    keywords = "ireland_shipwrecks"
    result = get_answers(pdf_file, keywords)
    if result:
        print(result)
    else:
        print("Failed to get answers. Check the logs for more information.")
