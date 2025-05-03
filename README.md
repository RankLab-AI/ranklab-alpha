# 🧪 ranklab-alpha

> _Optimize content for LLM visibility. Built on GEO-Bench insights. Demo-ready, future-focused._

**`ranklab-alpha`** is the prototype implementation of **RankLab AI**’s GEO optimization platform — an interactive lab for evaluating, treating, and scoring content visibility in LLM-powered search using research-backed methods from [GEO-Bench (KDD ’24)](https://doi.org/10.1145/3637528.3671900).


## 🧠 Tech Stack

- **FastAPI** – Backend API and server-rendered views
- **HTMX + Tachyons** – Minimalist frontend with no JS bundling
- **LLaMA 3.2** – Content rewriting and evaluation model
- **Firebase** – Auth and user data storage
- **SentenceTransformers, GPT-2, Custom Metrics** – GEO-style scoring logic


## 📁 Project Structure

```bash
ranklab-alpha/
│
├── app/                   # Core app (frontend/backend integration)
│   ├── main.py            # FastAPI entry point
│   ├── metrics.py         # Simple functions for computing metrics
│   ├── scoring.py         # Logic for scoring, treatments, benchmarks
│   ├── templates/         # Jinja templates for server-rendered views
│   └── treatments/        # Scripts or prompt templates for content treatments
│       ├── apply.py
│       └── prompts.py
│
├── benchmarks/            # GEO-Bench test slices (for evaluation)
│   └── examples/
│
├── data/                  # Pre-processed and example content samples
│
├── .env.example           # Sample environment variable config
├── .gitignore
├── requirements.txt       # Python dependencies
├── README.md
└── LICENSE
```

## 🚀 Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/RankLab-AI/ranklab-alpha.git
cd ranklab-alpha
```

### 2. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

Copy the sample `.env.example` and rename it to `.env`:
```bash
cp .env.example .env
```

Then fill in the following required values:
- `OPENAI_API_KEY`
- `FIREBASE_API_KEY`
- `FIREBASE_AUTH_DOMAIN`
- `FIREBASE_PROJECT_ID`
- `FIREBASE_APP_ID`
- `FIREBASE_CLIENT_EMAIL` and service key parts (if not using JSON path)
- `FIREBASE_SERVICE_ACCOUNT_JSON` (if using JSON credentials)
- `VENICE_API_KE`Y → **used for calling the Venice.ai enhanced LLM completions**

### 4. 🔐 Firebase Setup (Required for Auth)

To enable Firebase authentication:
1.	Go to Firebase Console.
2.	Select the project [ranklab-app](https://console.firebase.google.com/u/3/project/ranklab-app/overview)
3.	Navigate to **Project Settings** → **Service Accounts**.
4.	Click **Generate new private key**.
5.	Save the JSON file and place it in your project (e.g., /secrets/firebase-creds.json).
6.	In your .env file, set:
```bash
FIREBASE_SERVICE_ACCOUNT_JSON=secrets/firebase-creds.json
```

### 5. Run the App Locally

```bash
uvicorn app.main:app --reload
```