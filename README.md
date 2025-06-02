# Omisoft Pro Crypto Dashboard

**A professional cryptocurrency analytics dashboard providing real-time market insights, price tracking, historical data visualization, and AI-powered analysis for a wide range of cryptocurrencies.**

This project aims to offer a comprehensive and user-friendly platform for both enthusiasts and professionals to monitor and analyze the crypto market. It leverages data from CoinGecko and utilizes Cohere for AI-driven summaries and insights.

## ✨ Features

* **Real-time Price Data:** Get up-to-date pricing information for numerous cryptocurrencies.
* **Historical Price Charts:** Visualize price trends over various periods (24h, 7d, 30d, 1yr, Max).
* **Key Market Metrics:** Access important data like market cap, trading volume, rank, circulating supply, etc.
* **AI-Powered Summaries:** (If applicable, based on your Cohere integration) Concise, AI-generated summaries and sentiment analysis for selected cryptocurrencies.
* **Responsive Design:** Optimized for viewing on desktop, tablet, and mobile devices.
* **User-Friendly Interface:** Clean, intuitive, and themed interface for easy navigation and data consumption.
* **Search Functionality:** Quickly find and analyze specific cryptocurrencies.

## 🛠️ Tech Stack

* **Backend:** Python (Flask/FastAPI - *specify which one you are using*)
* **Frontend:** HTML, Tailwind CSS, JavaScript
* **Data Sources:**
    * [CoinGecko API](https://www.coingecko.com/en/api) for market data.
    * [Cohere API](https://cohere.com/) for AI-powered text generation (if integrated).
* **Deployment:** (Mention where you plan to deploy it, e.g., Heroku, Vercel, AWS, Self-hosted)

## 🚀 Getting Started

### Prerequisites

* Python 3.x
* `pip` (Python package installer)
* (Any other specific dependencies, e.g., a particular database if you add one)
* API Keys:
    * CoinGecko API Key (if required by your usage tier)
    * Cohere API Key (if using Cohere)

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/oaddou/cryptodashboard.git](https://github.com/oaddou/cryptodashboard.git)
    cd cryptodashboard
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # For Windows
    python -m venv venv
    .\venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(You'll need to create a `requirements.txt` file by running `pip freeze > requirements.txt` in your activated virtual environment after installing all necessary packages for your `app.py`)*

4.  **Set up environment variables:**
    Create a `.env` file in the root directory and add your API keys and any other configuration:
    ```env
    # Example .env file
    COHERE_API_KEY=your_cohere_api_key_here 
    # Add other variables like FLASK_APP, FLASK_ENV if using Flask
    # FLASK_APP=app.py
    # FLASK_DEBUG=True 
    ```
    *Ensure `.env` is listed in your `.gitignore` file (which it is in the one we created!).*

5.  **Run the application:**
    ```bash
    # If using Flask
    flask run

    # If using FastAPI with uvicorn (example)
    # uvicorn app:app --reload 
    ```
    *(Adjust the run command based on your Python backend framework and how `app.py` is set up.)*

6.  Open your browser and navigate to `http://127.0.0.1:5000` (or the port your application runs on).

## 📂 Project Structure (Example)


cryptodashboard/
├── venv/                   # Virtual environment (ignored by git)
├── static/                 # (Optional: if you have separate CSS/JS not in index.html)
│   └── css/
│   └── js/
├── templates/              # (Optional: if your Python backend serves HTML templates)
│   └── index.html          # (If not served directly as a static file)
├── app.py                  # Main Python backend application
├── index.html              # Main frontend file (if served as static or from root)
├── requirements.txt        # Python dependencies
├── .gitignore              # Files to be ignored by Git
├── README.md               # This file
└── .env                    # Environment variables (ignored by git)

*(Adjust this to reflect your actual project structure.)*

## 📈 Usage

1.  Enter the ID of the cryptocurrency you want to analyze (e.g., `bitcoin`, `ethereum`, `solana`) into the input field.
2.  Click the "Search" button.
3.  View the displayed information, including current price, market cap, historical chart, and AI summary.
4.  Use the dropdown to change the time range for the price chart.
5.  Click "Clear" to reset the output.

## 🤝 Contributing

Contributions are welcome! If you have suggestions for improvements or want to report a bug, please feel free to:

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a PullRequest

Please make sure to update tests as appropriate.

## 📄 License

Distributed under the [MIT License](LICENSE.md). See `LICENSE.md` for more information.
*(Choose a license like MIT if you want it to be open source. You'll need to add a LICENSE.md file if you specify one here.)*

## 🙏 Acknowledgements

* [CoinGecko API](https://www.coingecko.com/en/api)
* [Cohere API](https://cohere.com/)
* [Tailwind CSS](https://tailwindcss.com/)
* [Font Awesome](https://fontawesome.com/)

---

Contact: Omar Addou 
* LinkedIn: [linkedin.com/in/omaraddou](https://linkedin.com/in/omaraddou)
* X: [@oaddou83](https://x.com/oaddou83)
* GitHub: [oaddou](https://github.com/oaddou)
          https://oaddou.github.io/omar-addou-portfolio/

Project Link: [https://github.com/oaddou/cryptodashboard](https://github.com/oaddou/cryptodashboard)
