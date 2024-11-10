import os
import csv
import json
import time
import logging
from get_answers import get_answers

# Set up logging
logging.basicConfig(filename='error_log.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def list_pdf_folders(base_dir):
    return [f for f in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, f))]

def list_pdf_files(folder_path):
    return [f for f in os.listdir(folder_path) if f.endswith('.pdf')]

def try_parsing_json(answers_string, max_attempts=3):
    attempts = 0
    while attempts < max_attempts:
        try:
            print(f"Attempt {attempts + 1} to parse JSON...")
            # Find the start of the JSON content
            json_start = answers_string.find('{')
            json_end = answers_string.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_string = answers_string[json_start:json_end]
            else:
                json_string = answers_string

            # Remove any markdown code block syntax
            json_string = json_string.replace('```json', '').replace('```', '').strip()

            # Parse the JSON
            final_answers = json.loads(json_string)
            print("Parsed JSON successfully:", final_answers)
            print("Type of parsed JSON:", type(final_answers))
            return final_answers
        except json.JSONDecodeError as e:
            print("JSONDecodeError:", e)
            attempts += 1
            print(f"Attempt {attempts} failed. Retrying...")
            time.sleep(2)
    print("Failed to parse JSON after multiple attempts.")
    return None

def process_pdf(pdf_name, output_dir, keywords, csv_file_path):
    selected_pdf_path = os.path.join(output_dir, pdf_name)
    if not os.path.exists(selected_pdf_path):
        print(f"Selected PDF does not exist at path: {selected_pdf_path}")
        return
    answers = get_answers(selected_pdf_path, keywords)
    print(f"Raw answers string for {pdf_name}:", answers)
    if answers and "Agent stopped" not in answers:
        final_answers = try_parsing_json(answers)
        print(f"Parsed JSON answers for {pdf_name}:", final_answers)
    else:
        logging.error("The number of iterations has been reached; please consider increasing the limit if needed for this PDF.")
        fallback_answers = {}
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
        fallback_message = "The operation exceeded its iteration or time limit. Consider increasing the limit."
        for question in questions:
            fallback_answers[question] = fallback_message
        final_answers = [fallback_answers]
    if isinstance(final_answers, dict):
        final_answers = [final_answers]
    if isinstance(final_answers, list) and final_answers:
        for answer in final_answers:
            answer['PDF Name'] = pdf_name
        file_exists = os.path.isfile(csv_file_path)
        with open(csv_file_path, mode='a', newline='') as csv_file:
            fieldnames = ['PDF Name'] + list(final_answers[0].keys())
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            if not file_exists or os.stat(csv_file_path).st_size == 0:
                writer.writeheader()
            for answer in final_answers:
                writer.writerow(answer)
        print(f"Saved answers for {pdf_name} to {csv_file_path}")
    else:
        print(f"No valid answers to save for {pdf_name}.")

def main():
    base_dir = "/home/chethan/Desktop/Fianl_code/pdf"
    
    # List available folders
    folders = list_pdf_folders(base_dir)
    print("Available folders:")
    for i, folder in enumerate(folders, 1):
        print(f"{i}. {folder}")
    
    # Ask user to choose a folder
    while True:
        try:
            folder_choice = int(input("Enter the number of the folder you want to process: ")) - 1
            if 0 <= folder_choice < len(folders):
                selected_folder = folders[folder_choice]
                break
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a valid number.")
    
    output_dir = os.path.join(base_dir, selected_folder)
    keywords = selected_folder.replace('_', ' ')  # Convert folder name back to keywords
    
    # Create CSV file name based on the selected folder
    csv_file_name = f'{selected_folder}.csv'
    csv_file_path = os.path.join('/home/chethan/Desktop/Fianl_code', csv_file_name)
    
    # List PDFs in the selected folder
    pdf_list = list_pdf_files(output_dir)
    print('Available PDFs:')
    for i, pdf in enumerate(pdf_list, 1):
        print(f"{i}. {pdf}")
    
    # Ask user to choose PDFs to process
    while True:
        choice = input('Enter the number of the PDF to process, "all" to process all PDFs, or "q" to quit: ').strip().lower()
        if choice == 'q':
            break
        elif choice == 'all':
            for pdf in pdf_list:
                process_pdf(pdf, output_dir, keywords, csv_file_path)
            break
        else:
            try:
                pdf_index = int(choice) - 1
                if 0 <= pdf_index < len(pdf_list):
                    process_pdf(pdf_list[pdf_index], output_dir, keywords, csv_file_path)
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a valid number, 'all', or 'q'.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.exception("An unexpected error occurred:")
        print(f"An unexpected error occurred: {e}")
        print("Please check the error_log.log file for more details.")