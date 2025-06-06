from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
import requests
import cohere # Make sure to install the cohere library: pip install cohere
import numpy as np
import pandas as pd
from datetime import datetime
import io
import base64
import pytz
import matplotlib
matplotlib.use('Agg') # Ensure Matplotlib runs in a headless environment
import matplotlib.pyplot as plt
import traceback # For detailed error logging

# Load .env variables
load_dotenv()
COHERE_API_KEY = os.getenv('COHERE_API_KEY')
if not COHERE_API_KEY:
    print("Warning: COHERE_API_KEY not found in .env file. AI features will be disabled.")

app = Flask(__name__)

# Simple health check route
@app.route('/ping')
def ping():
    """Health check endpoint used by monitoring tools."""
    return jsonify({'status': 'ok'})

# --- Helper Functions ---
def fmt_num(val, decimals=0, is_currency=False):
    """Formats a number, optionally as currency. Returns 'N/A' on error."""
    prefix = "$" if is_currency else ""
    try:
        if val is None or val == 'N/A':
            return "N/A"
        if isinstance(val, str): 
            val = val.replace(',', '')
        
        num = float(val)
        if decimals == 0: 
            return f"{prefix}{int(num):,}"
        return f"{prefix}{num:,.{decimals}f}"
    except (ValueError, TypeError):
        return "N/A"

def get_trend_color_and_arrow(change_percentage_str):
    """Determines trend color and arrow based on percentage change."""
    try:
        if change_percentage_str is None:
            raise ValueError("Change percentage is None")
        change = float(change_percentage_str)
        if change >= 0:
            color = '#39FF14' # omisoft-primary / green
            arrow = '<span class="arrow-up text-omisoft-primary">&nbsp;▲</span>'
            trend_direction = "up"
        else:
            color = '#ff5252' # omisoft-warn / red
            arrow = '<span class="arrow-down text-omisoft-warn">&nbsp;▼</span>'
            trend_direction = "down"
    except (ValueError, TypeError):
        color = '#a7ffce' # omisoft-text-faint / neutral
        arrow = ''
        trend_direction = "neutral"
    return color, arrow, trend_direction

def build_changes_table(mkt_data):
    """Builds an HTML table for price changes over various periods."""
    periods = {
        '1h': mkt_data.get('price_change_percentage_1h_in_currency', {}).get('usd'),
        '24h': mkt_data.get('price_change_percentage_24h_in_currency', {}).get('usd'),
        '7d': mkt_data.get('price_change_percentage_7d_in_currency', {}).get('usd'),
        '14d': mkt_data.get('price_change_percentage_14d_in_currency', {}).get('usd'), # This might not directly map to dropdown, but is good info
        '30d': mkt_data.get('price_change_percentage_30d_in_currency', {}).get('usd'),
        '1y': mkt_data.get('price_change_percentage_1y_in_currency', {}).get('usd')
    }

    headers_html = "".join(f"<th>{period.upper()}</th>" for period in periods)
    
    cells_html = []
    for period_key, val in periods.items():
        trend_color, _, _ = get_trend_color_and_arrow(val)
        formatted_val = fmt_num(val, 2)
        cells_html.append(f'<td style="color:{trend_color};">{formatted_val}%</td>' if formatted_val != "N/A" else f'<td>N/A</td>')
    rows_html = f"<tr>{''.join(cells_html)}</tr>"
    
    return f"""
        <table class="changes-table w-full my-3 font-mono text-xs sm:text-sm">
          <thead>
            <tr>{headers_html}</tr>
          </thead>
          <tbody>
            {rows_html}
          </tbody>
        </table>
    """

def build_chart(coin_id, coin_name, days_str, overall_trend_color="#39FF14"):
    """Generates a base64 encoded price chart image."""
    try:
        # Convert days_str from HTML dropdown value to integer for dictionary keys and API
        # The HTML values are: "1", "7", "30", "90", "365", "max"
        if days_str == 'max':
            days_key_for_title = 'max'
            days_for_api = 'max' 
        else:
            days_key_for_title = int(days_str)
            days_for_api = str(days_key_for_title)
    except ValueError:
        days_key_for_title = 7 # Default key if conversion fails
        days_for_api = "7"   # Default for API

    chart_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    chart_params = {'vs_currency': 'usd', 'days': days_for_api} 
    
    try:
        chart_resp = requests.get(chart_url, params=chart_params, timeout=15)
        chart_resp.raise_for_status() 
        prices_data = chart_resp.json().get('prices')
        if not prices_data:
            return '<div class="error-msg text-omisoft-warn p-3 text-xs sm:text-sm">No price data available for chart.</div>'

        df = pd.DataFrame(prices_data, columns=['timestamp', 'price'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(7, 3), dpi=130)
        
        ax.plot(df['timestamp'], df['price'], color=overall_trend_color, linewidth=1.8)
        ax.set_facecolor('#191f1d')

        num_ticks = 5 
        if len(df) > num_ticks:
            ticks_idx = [int(i) for i in np.linspace(0, len(df) - 1, num_ticks)]
            ax.set_xticks(df['timestamp'].iloc[ticks_idx])
            date_format = '%d-%b' 
            
            if days_key_for_title == 1: 
                date_format = '%H:%M'
            elif isinstance(days_key_for_title, int) and days_key_for_title <= 7: 
                date_format = '%d %b' 
            elif days_key_for_title == 'max' or (isinstance(days_key_for_title, int) and days_key_for_title > 90): 
                 date_format = '%b-%y' 
            
            ax.set_xticklabels([d.strftime(date_format) for d in df['timestamp'].iloc[ticks_idx]], rotation=0, ha='center')
        
        # Synchronized chart_titles with HTML dropdown labels
        chart_titles_map = {
            1: "24h",    # Corresponds to value "1" in HTML
            7: "7d",     # Corresponds to value "7"
            30: "1m",    # Corresponds to value "30"
            90: "3m",    # Corresponds to value "90"
            365: "1y",   # Corresponds to value "365"
            "max": "Max" # Corresponds to value "max"
        }
        chart_title_display = chart_titles_map.get(days_key_for_title, f"{days_for_api} Days") # Fallback if key not found
        
        ax.set_title(f"{coin_name} • {chart_title_display}", color=overall_trend_color, fontsize=12, pad=10)

        ax.tick_params(axis='x', colors='#a7ffce', labelsize=8)
        ax.tick_params(axis='y', colors='#a7ffce', labelsize=9)
        for spine_pos in ['top', 'right']: 
            ax.spines[spine_pos].set_visible(False)
        for spine_pos in ['bottom', 'left']:
            ax.spines[spine_pos].set_color(overall_trend_color)
            ax.spines[spine_pos].set_linewidth(1.2)

        plt.tight_layout(pad=0.5) 
        img_io = io.BytesIO()
        plt.savefig(img_io, format='png', bbox_inches='tight', transparent=True)
        img_io.seek(0)
        img_base64 = base64.b64encode(img_io.getvalue()).decode()
        plt.close(fig) 
        return f'<img src="data:image/png;base64,{img_base64}" class="chart-img-animated rounded-lg border mt-2 mb-1 w-full" alt="{coin_name} Price Chart">'
    
    except requests.exceptions.RequestException as e:
        print(f"Chart API request error: {e}")
        return f'<div class="error-msg text-omisoft-warn p-3 text-xs sm:text-sm">Chart data temporarily unavailable (API Error).</div>'
    except Exception as e:
        print(f"Error building chart: {e}")
        traceback.print_exc()
        return f'<div class="error-msg text-omisoft-warn p-3 text-xs sm:text-sm">Error generating chart.</div>'

# --- Flask Routes ---
@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/api/crypto', methods=['POST'])
def crypto_api():
    """Fetches comprehensive crypto data and AI summary, returns as structured HTML."""
    try:
        req_data = request.get_json()
        if not req_data:
            return jsonify({'error': 'Invalid request. JSON payload expected.'}), 400

        coin_id = req_data.get('id', '').strip().lower()
        days_str = str(req_data.get('days', "7")) 

        if not coin_id:
            return jsonify({'error': 'Cryptocurrency ID is required.'}), 400

        cg_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
        cg_params = {
            'localization': 'false', 'tickers': 'false', 'market_data': 'true',
            'community_data': 'true', 'developer_data': 'true', 'sparkline': 'false'
        }
        
        try:
            r = requests.get(cg_url, params=cg_params, timeout=15)
            r.raise_for_status() 
            data = r.json()
        except requests.exceptions.HTTPError as http_err:
            if r.status_code == 404:
                 return jsonify({'error': f'No data found for "{coin_id}". Please check the ID.'}), 404
            return jsonify({'error': f'CoinGecko API error: {http_err}'}), r.status_code
        except requests.exceptions.RequestException as req_err:
            return jsonify({'error': f'Could not connect to CoinGecko API: {req_err}'}), 503

        if 'market_data' not in data:
            return jsonify({'error': f'Incomplete data received for "{coin_id}". Market data missing.'}), 500

        mkt = data['market_data']

        price_usd = mkt.get('current_price', {}).get('usd')
        mcap_usd = mkt.get('market_cap', {}).get('usd')
        fdv_usd = mkt.get('fully_diluted_valuation', {}).get('usd')
        volume_usd = mkt.get('total_volume', {}).get('usd')
        circ_supply = mkt.get('circulating_supply')
        total_supply = mkt.get('total_supply')
        max_supply = mkt.get('max_supply')
        rank = data.get('market_cap_rank')
        logo_url = data.get('image', {}).get('large', 'https://placehold.co/64x64/2a2f32/39FF14?text=N/A')
        coin_name = data.get('name', coin_id.title()) 
        symbol = data.get('symbol', '').upper()
        description_en = (data.get('description', {}).get('en', '') or '')[:800] 
        website_url = (data.get('links', {}).get('homepage', [None])[0] or "#")

        twitter_followers = data.get('community_data', {}).get('twitter_followers')
        reddit_subscribers = data.get('community_data', {}).get('reddit_subscribers')
        dev_stars = data.get("developer_data", {}).get("stars")
        dev_forks = data.get("developer_data", {}).get("forks")
        dev_total_issues = data.get("developer_data", {}).get("total_issues")
        
        high_24h_usd = mkt.get("high_24h", {}).get("usd")
        low_24h_usd = mkt.get("low_24h", {}).get("usd")
        ath_usd = mkt.get("ath", {}).get("usd")
        atl_usd = mkt.get("atl", {}).get("usd")
        
        price_change_24h_in_currency = mkt.get('price_change_percentage_24h_in_currency', {}).get('usd', 0.0)
        
        trend_color, price_arrow, trend_direction = get_trend_color_and_arrow(price_change_24h_in_currency)
        change_24h_display = f'<span class="text-omisoft-text-faint/80">({fmt_num(price_change_24h_in_currency, 2)}%)</span>'

        ai_summary_text = "AI analysis unavailable." 
        if COHERE_API_KEY:
            try:
                co = cohere.Client(COHERE_API_KEY) 
                
                user_content_for_ai = (
                    f"Analyze {coin_name} ({symbol}) as of {datetime.now(pytz.timezone('Europe/Amsterdam')).strftime('%d-%m-%Y %H:%M:%S')}."
                    f"\nCurrent Price: ${fmt_num(price_usd,4)}"
                    f"\nMarket Cap: ${fmt_num(mcap_usd)}"
                    f"\nFDV: ${fmt_num(fdv_usd)}"
                    f"\n24h Vol: ${fmt_num(volume_usd)}"
                    f"\n24h High: ${fmt_num(high_24h_usd,4)} | 24h Low: ${fmt_num(low_24h_usd,4)}"
                    f"\nCirculating Supply: {fmt_num(circ_supply)} | Total Supply: {fmt_num(total_supply)} | Max Supply: {fmt_num(max_supply)}"
                    f"\nDev stars: {fmt_num(dev_stars)} | Forks: {fmt_num(dev_forks)} | Issues: {fmt_num(dev_total_issues)}"
                    f"\nTwitter followers: {fmt_num(twitter_followers)} | Reddit subscribers: {fmt_num(reddit_subscribers)}"
                    f"\nDescription: {description_en}\nWebsite: {website_url}\n"
                )

                # Finetuned System Message
                system_prompt = (
                    "You are an expert crypto market analyst providing insights for executive decision-making. "
                    "Your analysis must be in concise, structured business English, avoiding jargon where possible, and without using hashtags or markdown formatting. "
                    "Before providing your analysis, you must first search for the latest news and developments about the requested cryptocurrency using web search tools. "
                    "Your response should include the following sections clearly:\n"
                    "1. Latest News & Developments: Begin by searching for and summarizing the most recent news, announcements, partnerships, or significant events related to this cryptocurrency from the past 30 days. Include specific dates and sources with URLs where possible.\n"
                    "2. Key Facts: A brief overview of the cryptocurrency.\n"
                    "3. Unique Value Proposition: What makes this coin stand out?\n"
                    "4. Recent Market Behavior: Summarize recent price action and trading patterns, incorporating insights from the latest news findings.\n"
                    "5. Bullish Scenario: Potential positive developments and their impact, referencing recent positive news if applicable.\n"
                    "6. Bearish Scenario: Potential risks and negative outlook, including any recent negative developments or concerns.\n"
                    "7. On-chain/Developer Activity (if available): Briefly mention relevant metrics and recent development updates.\n"
                    "8. Community Strength (if significant): Note community engagement and recent community-driven initiatives.\n"
                    "9. Market Sentiment Analysis: Based on recent news and social media trends, assess current market sentiment.\n"
                    "10. Practical Tips: One concise tip for beginners and one for experienced users, informed by current market conditions.\n"
                    "11. Official Website: State the official website.\n\n"
                    "12. AI Investment Perspective: Based on the comprehensive analysis above, provide a balanced investment outlook that synthesizes all the data points, recent news, market conditions, and risk factors. This should include potential entry points, risk management considerations, and timeline perspectives for different investor profiles.\n\n"
                    "SEARCH REQUIREMENTS:\n"
                    "- Always perform a web search for '[CRYPTO_NAME] news latest developments' before beginning your analysis\n"
                    "- Search for recent price movements, partnerships, technical updates, regulatory news, and market sentiment\n"
                    "- Prioritize information from the last 7-30 days\n"
                    "- Cite your sources appropriately when referencing news items\n\n"
                    "IMPORTANT DISCLAIMER (include verbatim at the end of your analysis):\n"
                    "This information should not be considered financial advice. Always conduct your own research and consult with qualified financial professionals before making any investment or financial decisions. Past performance does not guarantee future results, and all investments carry risk of loss."
                )

                messages = [
                    {"role": "SYSTEM", "message": system_prompt},
                    {"role": "USER", "message": user_content_for_ai} 
                ]
                                       
                chat_response = co.chat(
                    model="command-a-03-2025", 
                    message=messages[-1]["message"], 
                    chat_history=[messages[0]],
                    max_tokens=1024, 
                    temperature=0.1
                )
                ai_summary_text = chat_response.text.strip()

            except Exception as e:
                print(f"Cohere API error: {e}")
                traceback.print_exc()
                ai_summary_text = f"AI analysis unavailable due to an error: {str(e)[:100]}"
        else:
            ai_summary_text = "AI analysis disabled (API key not configured)."


        chart_html_content = build_chart(coin_id, coin_name, days_str, trend_color)
        changes_table_html = build_changes_table(mkt)
        
        now_nl_formatted = datetime.now(pytz.timezone("Europe/Amsterdam")).strftime('%d-%m-%Y %H:%M:%S')

        result_html_structure = f"""
        <div class="dashboard-output-wrap">
          <div class="hud-row flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 mb-3 p-2 rounded-md bg-black/20">
            <span class="hud-time text-omisoft-text-faint flex items-center gap-1">
                <i class="fas fa-clock text-omisoft-accent"></i> Local (NL): <b class="text-omisoft-text">{now_nl_formatted}</b>
            </span>
            <div class="flex gap-2">
                <span class="hud-badge ai bg-omisoft-primary/20 text-omisoft-primary px-2 py-1 rounded-md text-xs flex items-center gap-1">
                    <i class="fas fa-robot"></i>AI Analysis
                </span>
                <span class="hud-badge cg bg-omisoft-accent/20 text-omisoft-accent px-2 py-1 rounded-md text-xs flex items-center gap-1">
                    <i class="fas fa-chart-line"></i>Live Market Data
                </span>
            </div>
          </div>

          <div class="card-top flex items-center gap-3 sm:gap-4 mb-3 sm:mb-4 p-2 rounded-md bg-black/10">
            <img src="{logo_url}" alt="{coin_name} logo" class="coin-logo w-10 h-10 sm:w-12 sm:h-12 rounded-md">
            <div class="card-info flex-grow">
              <div class="card-title flex items-baseline gap-2 mb-0.5">
                <span class="coin-name text-omisoft-primary font-bold text-lg sm:text-xl">{coin_name}</span>
                <span class="coin-symbol text-omisoft-text-faint text-sm sm:text-base">({symbol})</span>
              </div>
              <div class="rank-mcap-row text-omisoft-text-faint text-xs sm:text-sm flex flex-col sm:flex-row sm:gap-3">
                <span class="coin-rank">Rank: <b class="text-omisoft-text">#{fmt_num(rank)}</b></span>
                <span class="coin-mcap">Market Cap: <b class="text-omisoft-text">{fmt_num(mcap_usd, 0, is_currency=True)}</b></span>
              </div>
              <div class="current-price-row text-omisoft-text-faint text-sm sm:text-base mt-1">
                <span class="current-label">Price:</span>
                <span class="current-price text-omisoft-primary font-bold text-base sm:text-lg">{fmt_num(price_usd, 4, is_currency=True)}</span>
                {price_arrow} {change_24h_display}
              </div>
            </div>
          </div>

          <div class="summary-box bg-[#20262a]/70 p-3 my-3 rounded-lg border border-[#222]/50">
            <div class="summary-title font-mono text-omisoft-accent mb-2 text-sm sm:text-base font-semibold flex items-center gap-2">
                <i class="fas fa-lightbulb"></i>AI Executive Summary
            </div>
            <div id="typewriter-output" class="typewriter-area font-mono text-omisoft-text text-xs sm:text-sm leading-relaxed min-h-[60px]">
                {ai_summary_text}
            </div>
            <div class="official-site font-mono text-xs sm:text-sm mt-2">
                Official site: <a href="{website_url}" target="_blank" rel="noopener noreferrer" class="text-omisoft-primary hover:underline">{website_url if website_url != "#" else "N/A"}</a>
            </div>
          </div>

          <div class="main-stats-row grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 sm:gap-3 mb-3 font-mono text-xs sm:text-sm">
            <div class="p-2 bg-[#191f1e]/80 rounded-md shadow-sm"><strong class="text-omisoft-text-faint/90 block text-[0.65rem] sm:text-[0.7rem] uppercase tracking-wider mb-0.5">FDV:</strong> <span class="text-omisoft-text text-sm sm:text-base">{fmt_num(fdv_usd, 0, is_currency=True)}</span></div>
            <div class="p-2 bg-[#191f1e]/80 rounded-md shadow-sm"><strong class="text-omisoft-text-faint/90 block text-[0.65rem] sm:text-[0.7rem] uppercase tracking-wider mb-0.5">24h Vol:</strong> <span class="text-omisoft-text text-sm sm:text-base">{fmt_num(volume_usd, 0, is_currency=True)}</span></div>
            <div class="p-2 bg-[#191f1e]/80 rounded-md shadow-sm"><strong class="text-omisoft-text-faint/90 block text-[0.65rem] sm:text-[0.7rem] uppercase tracking-wider mb-0.5">Circulating:</strong> <span class="text-omisoft-text text-sm sm:text-base">{fmt_num(circ_supply)}</span></div>
            <div class="p-2 bg-[#191f1e]/80 rounded-md shadow-sm"><strong class="text-omisoft-text-faint/90 block text-[0.65rem] sm:text-[0.7rem] uppercase tracking-wider mb-0.5">Total Supply:</strong> <span class="text-omisoft-text text-sm sm:text-base">{fmt_num(total_supply)}</span></div>
            <div class="p-2 bg-[#191f1e]/80 rounded-md shadow-sm"><strong class="text-omisoft-text-faint/90 block text-[0.65rem] sm:text-[0.7rem] uppercase tracking-wider mb-0.5">Max Supply:</strong> <span class="text-omisoft-text text-sm sm:text-base">{fmt_num(max_supply) if max_supply else "∞"}</span></div>
            <div class="p-2 bg-[#191f1e]/80 rounded-md shadow-sm"><strong class="text-omisoft-text-faint/90 block text-[0.65rem] sm:text-[0.7rem] uppercase tracking-wider mb-0.5">24h High:</strong> <span class="text-omisoft-text text-sm sm:text-base">{fmt_num(high_24h_usd, 4, is_currency=True)}</span></div>
            <div class="p-2 bg-[#191f1e]/80 rounded-md shadow-sm"><strong class="text-omisoft-text-faint/90 block text-[0.65rem] sm:text-[0.7rem] uppercase tracking-wider mb-0.5">24h Low:</strong> <span class="text-omisoft-text text-sm sm:text-base">{fmt_num(low_24h_usd, 4, is_currency=True)}</span></div>
            <div class="p-2 bg-[#191f1e]/80 rounded-md shadow-sm"><strong class="text-omisoft-text-faint/90 block text-[0.65rem] sm:text-[0.7rem] uppercase tracking-wider mb-0.5">ATH:</strong> <span class="text-omisoft-text text-sm sm:text-base">{fmt_num(ath_usd, 4, is_currency=True)}</span></div>
            <div class="p-2 bg-[#191f1e]/80 rounded-md shadow-sm"><strong class="text-omisoft-text-faint/90 block text-[0.65rem] sm:text-[0.7rem] uppercase tracking-wider mb-0.5">ATL:</strong> <span class="text-omisoft-text text-sm sm:text-base">{fmt_num(atl_usd, 4, is_currency=True)}</span></div>
            <div class="p-2 bg-[#191f1e]/80 rounded-md shadow-sm"><strong class="text-omisoft-text-faint/90 block text-[0.65rem] sm:text-[0.7rem] uppercase tracking-wider mb-0.5">Twitter:</strong> <span class="text-omisoft-text text-sm sm:text-base">{fmt_num(twitter_followers)}</span></div>
            <div class="p-2 bg-[#191f1e]/80 rounded-md shadow-sm"><strong class="text-omisoft-text-faint/90 block text-[0.65rem] sm:text-[0.7rem] uppercase tracking-wider mb-0.5">Reddit:</strong> <span class="text-omisoft-text text-sm sm:text-base">{fmt_num(reddit_subscribers)}</span></div>
            <div class="p-2 bg-[#191f1e]/80 rounded-md shadow-sm"><strong class="text-omisoft-text-faint/90 block text-[0.65rem] sm:text-[0.7rem] uppercase tracking-wider mb-0.5">Dev Stars:</strong> <span class="text-omisoft-text text-sm sm:text-base">{fmt_num(dev_stars)}</span></div>
          </div>

          <div class="changes-table-wrap">{changes_table_html}</div>
          <div id="chartSection" class="chart-section">{chart_html_content}</div>
        </div>
        """
        return jsonify({'html': result_html_structure, 'trend': trend_direction})

    except Exception as e:
        print("Error in /api/crypto:")
        traceback.print_exc()
        return jsonify({'error': f'An unexpected server error occurred: {str(e)}'}), 500


@app.route('/api/crypto_chart', methods=['POST'])
def crypto_chart_api():
    """Returns ONLY the new chart and changes table for a coin and new days range."""
    try:
        req_data = request.get_json()
        if not req_data:
            return jsonify({'error': 'Invalid request. JSON payload expected.'}), 400

        coin_id = req_data.get('id', '').strip().lower()
        days_str = str(req_data.get('days', "7"))

        if not coin_id:
            return jsonify({'error': 'Cryptocurrency ID is required.'}), 400

        cg_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
        cg_params = {'localization': 'false', 'tickers': 'false', 'market_data': 'true', 
                     'community_data': 'false', 'developer_data': 'false', 'sparkline': 'false'}
        try:
            r = requests.get(cg_url, params=cg_params, timeout=10)
            r.raise_for_status()
            data = r.json()
        except requests.exceptions.RequestException as req_err:
             return jsonify({'error': f'Could not connect to CoinGecko API for chart data: {req_err}'}), 503
        
        if 'market_data' not in data:
            return jsonify({'error': f'Incomplete market data for "{coin_id}" for chart.'}), 500

        mkt = data['market_data']
        coin_name = data.get('name', coin_id.title())
        
        price_change_for_trend = mkt.get(f'price_change_percentage_{days_str}d_in_currency', {}).get('usd')
        if price_change_for_trend is None : 
            price_change_for_trend = mkt.get('price_change_percentage_24h_in_currency', {}).get('usd', 0.0)

        trend_color, _, trend_direction = get_trend_color_and_arrow(price_change_for_trend)

        chart_html_content = build_chart(coin_id, coin_name, days_str, trend_color)
        changes_table_html = build_changes_table(mkt)
        
        return jsonify({
            'chart_html': chart_html_content,
            'changes_table': changes_table_html,
            'trend': trend_direction
        })

    except Exception as e:
        print(f"Error in /api/crypto_chart: {e}")
        traceback.print_exc()
        return jsonify({'error': f'An unexpected server error occurred while generating chart/table: {str(e)}'}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)
