import base64
import json
import os
import requests
import glob
from dotenv import load_dotenv
import argparse
import time

load_dotenv(override=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MEMBER_TOKEN = os.getenv("MEMBER_AUTH_TOKEN")
API_BASE_URL = "https://api.sadhak.sahaj.ai/xpensify"

# Define constants for the script
FILES_FOLDER_PATH = "receipts"

def ask_user_to_select_project(projects):
    print("\nAvailable Projects:")
    for i, p in enumerate(projects):
        print(f"{i + 1}. {p['timesheetName']}")

    while True:
        try:
            choice = int(input("\nSelect a project by number: "))
            if 1 <= choice <= len(projects):
                selected_project = projects[choice - 1]
                print(f"\n✔ Selected Project: {selected_project['timesheetName']}")
                return selected_project
            else:
                print("❌ Invalid choice. Try again.")
        except ValueError:
            print("❌ Enter a valid number.")




def setup():
    """Fetches currencies, expense types, and projects from the API."""
    print("-> Setup Agent: Fetching required data...")
    headers = {'Authorization': f'Bearer {MEMBER_TOKEN}'}

    try:
        print("👉 Fetching:", repr(API_BASE_URL))
        # Fetch Currency Types
        currencies_res = requests.get(f"{API_BASE_URL}/currency_types", headers=headers)
        currencies_res.raise_for_status()
        currencies = currencies_res.json()['data']
        print(f"-> Setup Agent: Found {len(currencies)} currencies.")

        # Fetch Expense Types
        expense_types_res = requests.get(f"{API_BASE_URL}/expense_type/?is_active=True", headers=headers)
        expense_types_res.raise_for_status()
        expense_types = expense_types_res.json()['data']
        print(f"-> Setup Agent: Found {len(expense_types)} active expense types.")

        # Fetch Projects
        projects_res = requests.get(f"{API_BASE_URL}/timesheets/", headers=headers)
        projects_res.raise_for_status()
        projects = projects_res.json()['timesheetNames']
        print(f"-> Setup Agent: Found {len(projects)} projects.")

        return {"currencies": currencies, "expense_types": expense_types, "projects": projects}
    except requests.exceptions.RequestException as e:
        print(f"❌ Setup Error: Failed to fetch data. {e}")
        raise

def run_extraction_agent(base64_file_data, mime_type, setup_data):
    """Analyzes the bill file using Gemini AI and returns structured data."""
    print("\n-> Extraction Agent: Analyzing bill with Gemini AI...")

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in your .env file.")

    valid_expense_type_names = [et['name'] for et in setup_data['expense_types']]
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

    system_prompt = f"""You are an intelligent expense processing agent. Analyze the provided bill file.
    1. Extract the following fields: date, vendor, amount (as a number), currency (the 3-letter symbol, e.g., USD, EUR, INR).
    2. For the date, find the primary date of the transaction and format it as YYYY-MM-DD.
    3. Classify the expense into ONE of the following categories: {json.dumps(valid_expense_type_names)}.
    4. Return the result as a single, valid JSON object with the keys: "date", "vendor", "amount", "currency", and "expenseType".
    If a value cannot be determined, set it to an empty string or null for amount."""

    payload = {
        "contents": [{"parts": [{"text": system_prompt}, {"inlineData": {"mimeType": mime_type, "data": base64_file_data}}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }

    response = requests.post(api_url, json=payload)
    response.raise_for_status()
    result = response.json()
    part = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0]
    time.sleep(5)

    if "text" in part:
        extracted_data = json.loads(part["text"])
        print("-> Extraction Agent: Successfully extracted data.")
        return extracted_data
    else:
        raise ValueError(f"Could not parse AI response: {json.dumps(result, indent=2)}")

def create_new_claim():
    """Creates a new claim and returns its PK."""
    print("\n-> Submission Agent: Creating new claim...")
    headers = {'Authorization': f'Bearer {MEMBER_TOKEN}'}
    params = {'role': 'User'}
    create_claim_res = requests.post(f"{API_BASE_URL}/claim", headers=headers, params=params, json={})
    create_claim_res.raise_for_status()
    claim_data = create_claim_res.json()
    claim_pk = claim_data['claim_pk']
    print(f"Successfully created claim with ID: {claim_pk}")
    return claim_pk

def update_claim_title(claim_pk, title):
    """Updates the title of an existing claim."""
    print(f"-> Submission Agent: Updating title for claim {claim_pk}...")
    headers = {'Authorization': f'Bearer {MEMBER_TOKEN}'}
    params = {'role': 'User'}
    update_title_res = requests.put(f"{API_BASE_URL}/claim/{claim_pk}", headers=headers, params=params, json={'title': title})
    update_title_res.raise_for_status()
    print(f"Successfully set title to: '{title}'")

def delete_claim(claim_pk):
    """Deleting the created Draft claim.""" 
    headers = {'Authorization': f'Bearer {MEMBER_TOKEN}'}
    params = {'role': 'User'}
    delete_res = requests.delete(f"{API_BASE_URL}/claim/{claim_pk}", headers=headers, params=params)
    delete_res.raise_for_status()
    print(f"Claim deleted as intermediate step failed")

def add_expense_to_claim(claim_pk, extracted_data, setup_data, file_data, file_path, mime_type, selected_project):
    """Adds a single expense and its corresponding bill to an existing claim."""
    print(f"\n-> Submission Agent: Adding expense from '{os.path.basename(file_path)}' to claim {claim_pk}...")
    headers = {'Authorization': f'Bearer {MEMBER_TOKEN}'}
    params = {'role': 'User'}

    try:
        # Step A: Prepare and create the expense
        print("  [Sub-step A] Creating expense...")
        expense_type_id = next((et['id'] for et in setup_data['expense_types'] if et['name'] == extracted_data['expenseType']), None)
        timesheet_id = selected_project["timesheetId"]

        if not expense_type_id: raise ValueError(f"Could not find ID for expense type: {extracted_data['expenseType']}")
        if not timesheet_id: raise ValueError(f"Could not find ID for project: {selected_project}")

        expense_payload = {
            "amount": extracted_data['amount'],
            "currency_type_symbol": extracted_data['currency'],
            "date_of_expense": f"{extracted_data['date']}T00:00:00.000Z",
            "expense_type_id": expense_type_id,
            "project_id": timesheet_id,
            "user_comment": "",
            "vendor": extracted_data['vendor']
        }
        print("  Expense Payload:")
        print(json.dumps(expense_payload, indent=2))

        create_expense_res = requests.post(f"{API_BASE_URL}/claim/{claim_pk}/expense", headers=headers, params=params, json=expense_payload)
        create_expense_res.raise_for_status()
        expense_res_data = create_expense_res.json()
        expense_id = expense_res_data['id']
        print(f"  Successfully created expense with ID: {expense_id}")

        # Step B: Upload the bill file
        print(f"  [Sub-step B] Uploading bill for expense {expense_id}...")
        files = {'file': (os.path.basename(file_path), file_data, mime_type)}
        upload_bill_res = requests.post(f"{API_BASE_URL}/claim/{claim_pk}/expense/{expense_id}/bill", headers=headers, params=params, files=files)
        upload_bill_res.raise_for_status()
        print(f"  Successfully uploaded bill. Status Code: {upload_bill_res.status_code}")
        print(f"  -> Finished processing '{os.path.basename(file_path)}'.")

    except requests.exceptions.RequestException as e:
        print(f"❌ Submission Agent Error for '{os.path.basename(file_path)}': API call failed. {e}")
        if e.response is not None:
            print(f"Response Body: {e.response.text}")
        raise

def parse_arguments():
    parser = argparse.ArgumentParser(description="Process expense claim files and submit to Xpensify.")
    parser.add_argument("--claim-title", required=True, help="Title for the new claim.")
    return parser.parse_args()


def main():
    """Main function to orchestrate the expense claim process."""
    claim_pk = None
    try:
        args = parse_arguments()
        CLAIM_TITLE = args.claim_title
        if not MEMBER_TOKEN or not GEMINI_API_KEY:
            raise ValueError("MEMBER_TOKEN and GEMINI_API_KEY must be set in the .env file.")

        print(f"-> Orchestrator: Searching for files in '{FILES_FOLDER_PATH}'...")
        if not os.path.isdir(FILES_FOLDER_PATH):
            raise FileNotFoundError(f"The specified file folder does not exist: {FILES_FOLDER_PATH}")

        supported_extensions = ["*.jpg", "*.jpeg", "*.png","*.pdf"]
        file_paths = []
        for ext in supported_extensions:
            file_paths.extend(glob.glob(os.path.join(FILES_FOLDER_PATH, ext)))

        if not file_paths:
            raise FileNotFoundError(f"No files (.jpg, .jpeg, .png, .pdf) found in '{FILES_FOLDER_PATH}'.")

        print(f"-> Orchestrator: Found {len(file_paths)} files to process.")

        # 1. Run Setup once
        setup_data = setup()

        # Ask user to select a project
        selected_project = ask_user_to_select_project(setup_data["projects"])


        # 2. Create a single new claim
        claim_pk = create_new_claim()
        update_claim_title(claim_pk, CLAIM_TITLE)

        # 3. Loop through each file and process it
        total_expenses = len(file_paths)
        for index, current_file_path in enumerate(file_paths):
            print("\n" + "-"*50)
            print(f"Processing Expense {index + 1} of {total_expenses}: {os.path.basename(current_file_path)}")
            print("-"*50)

            with open(current_file_path, "rb") as file:
                data = file.read()
            base64_file_data = base64.b64encode(data).decode('utf-8')

            file_extension = os.path.splitext(current_file_path)[1].lower()
            if file_extension in ['.jpeg', '.jpg']:
                mime_type = 'image/jpeg'
            elif file_extension == '.png':
                mime_type = 'image/png'
            elif file_extension == '.pdf':
                mime_type = 'application/pdf'
            else:
                raise ValueError(f"Unsupported file extension: {file_extension}")
            
            print(f"Detected file type: {mime_type}")

            extracted_data = run_extraction_agent(base64_file_data, mime_type, setup_data)
            print("\n--- Extracted Data from AI ---")
            print(json.dumps(extracted_data, indent=2))

            add_expense_to_claim(claim_pk, extracted_data, setup_data, data, current_file_path, mime_type,selected_project)

        final_url = f"https://sadhak.sahaj.ai/xpensify/user/claims/{claim_pk}/expenses"
        print("\n" + "="*50)
        print(f"✅ All {total_expenses} expenses processed successfully under claim {claim_pk}!")
        print(f"View your claim here: {final_url}")
        print("="*50)

    except Exception as error:
        print(f"\n❌ An error occurred during the orchestration: {error}")
        if claim_pk:
            delete_claim(claim_pk=claim_pk)

# --- Script Execution ---

if __name__ == "__main__":
    main()

