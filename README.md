# Xpensify Draft Claim AI Agent

This project processes receipt files (images) and generates a **draft claim link** after running through the notebook step by step.

---


## Setup 

### Clone the Repository

Clone and chnage current directory to xpensify_draft_claim_ai_agent

### Create virtual environment and activate(mac)

```bash
python3 -m venv venv
source venv/bin/activate
```

### Install Requirements

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Set Environment Variables

Create a .env file in the root of the project with your keys/tokens.
Example (.env.example):
```bash
GEMINI_API_KEY=your_gemini_api_key
MEMBER_TOKEN=your_member_token
XPENSIFY_BASE_URL=https://xpensify.sahaj.ai/api/v1 (based on env)
```

### Prepare the Receipts Folder

Create a receipts/ folder and place your bill images here.

### Run the Notebook

1. Open xpensify_claim_generator.ipynb.

2. Run each code block in order, one by one.

3. After executing the last block in the notebook, a claim draft link will be generated in the output.





