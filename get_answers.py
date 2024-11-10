import os
import json
from crewai import Agent, Task, Crew, Process
from crewai_tools import PDFSearchTool
import logging


# Set API key
api_key = "sk-proj-7NJnI5kRLgtjm8o0u01pT3BlbkFJxLa4VTeTJcUNxAh3b2ol"
os.environ['OPENAI_API_KEY'] = api_key

# Function to get PDF file paths from a folder
def get_pdf_filepaths(folder_name):
    try:
        # Get the absolute path of the folder
        folder_path = os.path.abspath(folder_name)
        # List all PDF files in the folder
        pdf_files = [os.path.join(folder_path, file) for file in os.listdir(folder_path) if file.endswith('.pdf')]
        return pdf_files
    except Exception as e:
        print(f"Error in getting PDF file paths: {e}")
        return []

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

# Creating the PDF search tool
pdf_tool = PDFSearchTool()

# Creating the agent
pdf_agent = Agent(
    role='PDF Researcher',
    goal='Extract specific information from given PDF files.',
    memory=True,
    max_iter=75,
    backstory=(
        "You are an expert in extracting and analyzing data from PDF documents, "
        "focusing on historical and environmental research."
    ),
    tools=[pdf_tool]
)

# Creating the task
pdf_task = Task(
    description=(
        "Given a PDF path: {pdf_path}, extract answers to the following questions:\n" 
        "\n".join(questions) +
        "\nYour final answer MUST be in JSON format with the questions as keys."
    ),
    expected_output='A json format object containing the answers to the specified questions.',
    tools=[pdf_tool],
    agent=pdf_agent
)

# Forming the crew
crew = Crew(
    agents=[pdf_agent],
    tasks=[pdf_task],
    process=Process.sequential
)

# Function to kick off the crew
def kickoff_crew(pdf_path):
    try:
        inputs = {'pdf_path': pdf_path}
        result = crew.kickoff(inputs=inputs)
        return pdf_task.output.raw
    except Exception as e:
        print(f"Error during kickoff: {e}")
        return None

# Updated get_answers function to include folder-based organization
def get_answers(pdf_file, keywords):
    try:
        pdf_folder_path = f'pdf/{keywords.replace(" ", "_")}'
        all_pdfs = get_pdf_filepaths(pdf_folder_path)
        final_pdf = None
        
        for pdf in all_pdfs:
            if pdf_file in pdf:
                final_pdf = pdf
                break

        if final_pdf is None:
            print('PDF file not found. Please check the path and try again.')
            return None
        
        # Kick off the process
        result = kickoff_crew(final_pdf)
        
        # Check if the result is an error message
        if result and "Agent stopped" in result:
            logging.error("Process stopped due to iteration limit or time limit.")
            return None
        
        # Handle if the result is None or an unexpected response
        if not result:
            logging.error("No result was returned or an error occurred during the process.")
            return None
        
        return result
    
    except Exception as e:
        logging.error(f"Error in get_answers function: {e}")
        return None
