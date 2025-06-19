# 🧪 ranklab-alpha

> _Optimize content for LLM visibility. Built on GEO-Bench insights. Demo-ready, future-focused._

**`ranklab-alpha`** is the prototype implementation of **RankLab AI**’s GEO optimization platform — an interactive lab for evaluating, treating, and scoring content visibility in LLM-powered search using research-backed methods from [GEO-Bench (KDD ’24)](https://doi.org/10.1145/3637528.3671900).


## 🧠 Tech Stack

- **FastAPI** – Backend API and server-rendered views
- **HTMX + Tailwind CSS** – Minimalist, utility-first frontend with no JavaScript bundling
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

Then fill in the following values using the Firebase Console:
- `FIREBASE_API_KEY`: Go to **Project Settings → General → Your Apps → Firebase SDK snippet (Config)**
- `FIREBASE_AUTH_DOMAIN`: Same section as above
- `FIREBASE_PROJECT_ID`: Found under **Project Settings → General**
- `FIREBASE_APP_ID`: In **Firebase SDK snippet (Config)**

Then fill in the remaining required values:
- `FIREBASE_SERVICE_ACCOUNT_JSON` (for using JSON credentials)
- `VENICE_API_KEY` → **used for calling the Venice.ai enhanced LLM completions**
- `GROQ_API_KEY` → **used for accessing Groq-hosted LLM models**

> ℹ️ These API keys are required for advanced LLM processing and content rewriting. If not provided, some treatments may be unavailable or fallback to basic completions.

### 4. Firebase Setup and Service Account

To enable authentication and admin operations in your Firebase project, follow these steps to set up Firebase and obtain a Service Account JSON file:

#### 1. Set Up a Firebase Project from Scratch

> 💡 **Note:** As of now, RankLab Alpha has not onboarded any clients, so you are free to set up a brand new Firebase project and database from scratch. There is no requirement to connect to an existing instance.

1. Visit the [Firebase Console](https://console.firebase.google.com/) and create a new project (or select an existing one).
2. Go to **Project Settings → General → Your apps** and register your app (choose "Web" if asked).
3. Enable **Email/Password Authentication**:
   - Navigate to **Authentication → Sign-in method**.
   - Enable the **Email/Password** provider.

4. Set up **Cloud Firestore**:
   - Go to **Firestore Database**.
   - Click **Create Database** and choose **Start in test mode** (recommended for dev).

#### 2. Generate Service Account Key

1. In the **Firebase Console**, navigate to **Project Settings → Service Accounts**.
2. Click **Generate new private key** and confirm.
3. Download the resulting JSON file and save it to your project root as:

   ```
   firebase-admin.creds.json
   ```

4. In your `.env` file, add:

   ```
   FIREBASE_SERVICE_ACCOUNT_JSON=firebase-admin.creds.json
   ```

> 🛑 This project’s `.gitignore` already excludes any `*.creds.json` files, so this file will not be committed to version control if you follow the naming convention above.

This setup enables authentication and Firestore access in development and production.

### 5. Run the App Locally

```bash
uvicorn app.main:app --reload
```

## 🚢 Deployment

You can deploy RankLab Alpha quickly using services like [Render](https://render.com/), which support FastAPI and static file hosting.

### Render Deployment Steps

1. **Push your code to GitHub**  
   Ensure your repository is hosted on GitHub and the latest changes are committed.

2. **Create a new Web Service on Render**  
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click **New → Web Service**
   - Connect your GitHub repository

3. **Configure build settings**  
   - **Environment:** Python 3.11 or higher
   - **Build Command:**  
     ```
     pip install -r requirements.txt
     ```
   - **Start Command:**  
     ```
     uvicorn app.main:app --host 0.0.0.0 --port 8000
     ```

4. **Set Environment Variables**  
   In the **Environment** section, add all required variables from your `.env` file:
   - `FIREBASE_API_KEY`
   - `FIREBASE_AUTH_DOMAIN`
   - `FIREBASE_PROJECT_ID`
   - `FIREBASE_APP_ID`
   - `FIREBASE_SERVICE_ACCOUNT_JSON`
   - `FIREBASE_STORAGE_BUCKET`
   - `VENICE_API_KEY`
   - `GROQ_API_KEY`

5. **Upload Service Account File (if needed)**  
   You can upload your `firebase-admin.creds.json` via the Render **Secret Files** feature or manually reference it in your `.env`.

6. **Deploy**  
   Click **Create Web Service** and Render will build and deploy your app.

> ✅ Tip: Render auto-deploys on new commits to your GitHub repo. You can configure deploy hooks or manual redeploys as needed.

## 🤝 Contributing

Thank you for your interest in contributing to RankLab Alpha! This is an early-stage prototype, and we welcome well-structured contributions that preserve clarity and maintainability.

### Ground Rules

* **NEVER commit directly to `main`.** Always create a feature or fix branch (e.g. `feature/add-treatment-x`).
* Keep code **modular, minimal, and readable**.
* Respect the code style. Use automatic formatting before committing.

### Code Formatting

We use [`ruff`](https://docs.astral.sh/ruff/) for formatting and linting.

#### Install Ruff

```bash
pip install ruff
```

#### Format Files

To format all treatment files:

```bash
ruff format --line-length 100 app/treatments/*.py
```

To format all app-level modules:

```bash
ruff format --line-length 100 app/*.py
```

### Alternative: Using `black`

If you prefer [`black`](https://black.readthedocs.io/en/stable/):

```bash
pip install black
black -l 100 app/*.py
```

You can also configure formatting tools via `pyproject.toml` (ask if you'd like to add this).

### Summary

* Follow formatting rules using `ruff` or `black`
* Work on a separate branch, not `main`
* Keep changes focused and clearly scoped
* Avoid breaking existing functionality

Feel free to open an issue or discussion before implementing large changes.
