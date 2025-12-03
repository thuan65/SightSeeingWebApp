import google.generativeai as genai
import sqlite3
import os
import json
import time
import logging
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()

# 2. Configure Logging (Clean format, no icons)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vietnam_travel_db.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


class VietnamBuilder:
    def __init__(self, db_name="vietnam_travel.db", base_delay=4):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.db_name = db_name
        self.base_delay = base_delay  # Seconds to wait after a successful request

        # List of Major Cities (Tier 1) - Target: > 100 places
        self.tier1_cities = [
            "Ha Noi", "Ho Chi Minh", "Da Nang", "Lam Dong",  # Da Lat
            "Khanh Hoa", "Quang Ninh", "Thua Thien Hue", "Kien Giang",  # Phu Quoc
            "Quang Nam", "Ba Ria - Vung Tau", "Lao Cai", "Ninh Binh",
            "Hai Phong", "Can Tho"
        ]

        # Full list of 63 Provinces in Vietnam
        self.all_provinces = [
            "An Giang", "Ba Ria - Vung Tau", "Bac Giang", "Bac Kan", "Bac Lieu",
            "Bac Ninh", "Ben Tre", "Binh Dinh", "Binh Duong", "Binh Phuoc",
            "Binh Thuan", "Ca Mau", "Can Tho", "Cao Bang", "Da Nang",
            "Dak Lak", "Dak Nong", "Dien Bien", "Dong Nai", "Dong Thap",
            "Gia Lai", "Ha Giang", "Ha Nam", "Ha Noi", "Ha Tinh",
            "Hai Duong", "Hai Phong", "Hau Giang", "Hoa Binh", "Hung Yen",
            "Khanh Hoa", "Kien Giang", "Kon Tum", "Lai Chau", "Lam Dong",
            "Lang Son", "Lao Cai", "Long An", "Nam Dinh", "Nghe An",
            "Ninh Binh", "Ninh Thuan", "Phu Tho", "Phu Yen", "Quang Binh",
            "Quang Nam", "Quang Ngai", "Quang Ninh", "Quang Tri", "Soc Trang",
            "Son La", "Tay Ninh", "Thai Binh", "Thai Nguyen", "Thanh Hoa",
            "Thua Thien Hue", "Tien Giang", "Ho Chi Minh", "Tra Vinh",
            "Tuyen Quang", "Vinh Long", "Vinh Phuc", "Yen Bai"
        ]

        # Initialize DB and AI Model
        self.setup_db()
        self.setup_gemini()

    def setup_db(self):
        """Initialize SQLite database and table."""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS places (
            id INTEGER PRIMARY KEY,
            name TEXT, 
            province TEXT, 
            category TEXT, 
            description TEXT,
            UNIQUE(name, province)
        )''')
        conn.commit()
        conn.close()

    def setup_gemini(self):
        """Configure Gemini API client."""
        if not self.gemini_key:
            logging.error("GEMINI_API_KEY missing in .env file.")
            raise ValueError("Missing API Key")

        try:
            genai.configure(api_key=self.gemini_key)
            # Using 'gemini-1.5-flash' for speed and stability
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logging.info("Connected to Gemini-1.5-Flash successfully.")
        except Exception as e:
            logging.error(f"Failed to configure AI: {e}")
            raise

    def ask_gemini(self, prompt, retries=5):
        """Send request to AI with Exponential Backoff."""
        for i in range(retries):
            try:
                # Send request
                response = self.model.generate_content(prompt)

                if not response.text:
                    raise ValueError("Empty response from AI")

                # Clean JSON string (remove markdown)
                text_clean = response.text.replace('```json', '').replace('```', '').strip()

                # Attempt to parse JSON
                try:
                    data = json.loads(text_clean)
                except json.JSONDecodeError:
                    # Fallback: find list brackets
                    start = text_clean.find('[')
                    end = text_clean.rfind(']') + 1
                    if start != -1 and end != -1:
                        data = json.loads(text_clean[start:end])
                    else:
                        raise ValueError("Invalid JSON format")

                # Success -> Wait and return
                logging.info(f"[SUCCESS] Response received. Waiting {self.base_delay}s...")
                time.sleep(self.base_delay)
                return data

            except Exception as e:
                # Error -> Wait with exponential backoff
                wait_time = 5 * (2 ** i)
                logging.warning(f"[WARNING] Attempt {i + 1}/{retries} failed: {str(e)[:100]}...")
                logging.warning(f"[WAIT] Cooling down for {wait_time}s...")
                time.sleep(wait_time)

        logging.error("[ERROR] Max retries reached. Skipping request.")
        return []

    def save_to_db(self, data, province):
        """Insert data into SQLite."""
        if not data: return
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        count = 0
        for item in data:
            try:
                c.execute('''
                    INSERT OR IGNORE INTO places (name, province, category, description)
                    VALUES (?, ?, ?, ?)
                ''', (item.get('name'), province, item.get('category'), item.get('desc')))
                if c.rowcount > 0: count += 1
            except Exception:
                pass
        conn.commit()
        conn.close()
        logging.info(f"[DB] Saved +{count} new places for {province}.")

    def scan_province(self, province):
        """Main logic to scan a specific province."""

        # Strategy for Tier 1 Cities (Deep Scan)
        if province in self.tier1_cities:
            logging.info(f"[SCANNING] Tier 1 City: {province}")
            categories = [
                "Historical Sites & Museums",
                "Nature & Landscapes",
                "Spiritual Sites (Temples, Churches)",
                "Entertainment & Shopping",
                "Local Cuisine & Night Markets",
                "Coffee Shops & Art Spaces"
            ]
            for cat in categories:
                logging.info(f"   -> Category: {cat}")
                prompt = f"""
                List 20 famous locations related to "{cat}" in {province}, Vietnam.
                Return strictly a JSON List: [{{"name": "Location Name", "category": "{cat}", "desc": "Short description"}}]
                """
                results = self.ask_gemini(prompt)
                self.save_to_db(results, province)

        # Strategy for Tier 2 Provinces (Standard Scan)
        else:
            logging.info(f"[SCANNING] Tier 2 Province: {province}")
            prompt = f"""
            Act as a local tour guide. List 25 distinct sightseeing spots in {province}, Vietnam.
            Prioritize specific landmarks over general areas.
            Return strictly a JSON List: [{{"name": "Location Name", "category": "General", "desc": "Short description"}}]
            """
            results = self.ask_gemini(prompt)
            self.save_to_db(results, province)

    def run(self):
        logging.info("STARTING FULL VIETNAM SCAN...")
        total = len(self.all_provinces)

        for i, province in enumerate(self.all_provinces):
            logging.info(f"--- Processing [{i + 1}/{total}]: {province} ---")
            self.scan_province(province)

            logging.info("[SLEEP] Pausing 3s before next province...")
            time.sleep(3)

        logging.info("SCAN COMPLETED.")


if __name__ == "__main__":
    try:
        # Clear old log file
        if os.path.exists("vietnam_travel_db.log"):
            open("vietnam_travel_db.log", "w").close()

        bot = VietnamBuilder(base_delay=4)
        bot.run()
    except KeyboardInterrupt:
        print("\n[STOP] Process interrupted by user.")
    except Exception as e:
        print(f"\n[CRITICAL ERROR] {e}")