# Xpensify Draft Claim AI Agent

Xpensify Draft Claim AI Agent is an automated tool that scans receipt images, extracts expense details using Google Gemini AI, and creates a draft claim in Xpensify — all in one command.

### The workflow is:

- You place all your bill images inside the receipts/ folder

- Run the given command after the setup

### The tool:

- Reads each bill image

- Extracts vendor, date, amount, expense type

- Maps it into Xpensify expense format

- Creates a new claim

- Uploads all expenses under that claim

- Prints a draft claim link at the end


---


## Setup 

### Clone the Repository

Clone and change current directory to xpensify_draft_claim_ai_agent

### Set Environment Variables

Create a .env file in the root of the project with your keys/tokens.

Example (.env.example):

```bash
GEMINI_API_KEY=your_gemini_api_key
MEMBER_TOKEN=your_member_token
```


#### 🔑 How to Generate Required Keys
✔ GEMINI_API_KEY

Get your Gemini API key here (Google AI Studio):
👉 https://aistudio.google.com/app/apikey

#### ✔ MEMBER_TOKEN

Login to sadhak.sahaj.ai, open DevTools → Network, trigger any API call, and copy the Authorization Bearer token.
Use that token as MEMBER_TOKEN

### Prepare the Receipts Folder

In the receipts/ folder place your bill images (remove he sample one present).

### Run the command


```bash
make run CLAIM_TITLE="claim title here"
```
### Common Errors

1️⃣ 401 Unauthorized

This error means your MEMBER_TOKEN is invalid or expired. 
- re-populate the member auth token from sadhak.

2️⃣ 429/503 Too Many Requests (Gemini API Rate Limit/Service Unavailable)

This happens when Gemini receives too many requests in a short time.
 - Wait a few seconds and retry

 - If it continues, generate a new API key


## Current Limitations & Future Improvements

- Currently supports only .jpg and .jpeg images
(support for PNG, PDF, and other formats can be added easily)

- Uses Google Gemini API directly; rate limits may apply

- Can be converted into a web-based chat interface using Google ADK (Web Chat)

- Logic can be extended to multi-project selection,multiple claims generation. 









