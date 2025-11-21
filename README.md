# Turku Auto-Center Trade-in Valuation Tool

An internal tool for evaluating car trade-ins using Google's Gemini AI.

## Features
- **Mobile-first**: Uses camera input for easy use on the lot.
- **Local Context**: Applies Turku-specific market rules (Diesel vs EV).
- **Fraud Detection**: Checks background for authentic Nordic environment.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **API Key**:
    - Get a Google Gemini API key from [Google AI Studio](https://aistudio.google.com/).
    - Copy `.env.example` to `.env` and paste your key:
        ```bash
        cp .env.example .env
        # Edit .env
        ```
    - Alternatively, you can enter the key in the app sidebar.

## Running the App

```bash
streamlit run app.py
```

## Usage
1.  Open the app in your browser (or mobile browser if on same network).
2.  Allow camera access.
3.  Take a photo of the car.
4.  Read the Senior Buyer's evaluation.
