import json
import mysql.connector
import re # Make sure to import re for regex
from flask import Flask, request, jsonify
from flask_cors import CORS # Needed to allow your frontend to talk to your backend

# --- Database Configuration ---
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '-Z0]({779hNZZ2iNpx<b-1h!=', # Your MySQL password here
    'database': 'credit_card_advisor_db'
}

# --- Database Manager Class ---
class DatabaseManager:
    def __init__(self, db_config):
        self.db_config = db_config
        self.connection = None

    def connect(self):
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            if self.connection.is_connected():
                print("DEBUG: Database connection successful.")
        except mysql.connector.Error as e:
            print(f"Error: Could not connect to database: {e}")
            self.connection = None

    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("DEBUG: Database connection closed.")

    def fetch_credit_cards_by_criteria(self, income=None, reward_preference=None, category_preference=None, perks_preference=None):
        self.connect()
        cards = []
        if not self.connection:
            return cards

        cursor = self.connection.cursor(dictionary=True)
        query = "SELECT * FROM credit_cards WHERE 1=1"
        params = []

        if income is not None:
            query += " AND min_income <= %s"
            params.append(income)

        try:
            cursor.execute(query, params)
            cards = cursor.fetchall()
            print(f"DEBUG: Fetched {len(cards)} cards from DB (before ALL Python-side filters) for income: {income}.")
        except mysql.connector.Error as e:
            print(f"Error fetching cards from DB: {e}")
        finally:
            cursor.close()
            self.close()
        return cards

# --- Utility Functions ---
def parse_user_query(query):
    query_lower = query.lower()
    parsed_data = {
        'income': None,
        'spending': {},
        'reward_preference': None,
        'category_preference': None,
        'perks_preference': None
    }

    # Parse income more specifically
    # Look for phrases like "my income is X", "I earn X", "I make X"
    income_patterns = [
        r"(?:my monthly income is|i earn|i make|my income is)\s*(\d+)",
        r"income\s*is\s*(\d+)"
    ]
    for pattern in income_patterns:
        match = re.search(pattern, query_lower)
        if match:
            income_val = int(match.group(1))
            if 10000 <= income_val <= 500000: # Ensure income is within a reasonable range
                parsed_data['income'] = float(income_val)
                break
    # Fallback: if no specific income phrase found, try to find a standalone large number within range
    if parsed_data['income'] is None:
        all_numbers = [int(s) for s in query_lower.split() if s.isdigit()]
        for num in all_numbers:
            if 10000 <= num <= 500000: # Assuming income is a larger number in this range
                parsed_data['income'] = float(num)
                break


    # Parse spending
    # Using more flexible patterns to capture numbers before keywords
    spending_keywords = {
        'online shopping': 'online_shopping',
        'online': 'online_shopping', # 'online' alone should also map to online_shopping
        'groceries': 'groceries',
        'fuel': 'fuel',
        'travel': 'travel',
        'dining': 'dining'
    }
    for keyword, category in spending_keywords.items():
        # Pattern to capture a number possibly followed by "on" or "for", then the keyword
        pattern = rf"(\d+)\s*(?:on|for)?\s*{re.escape(keyword)}"
        match = re.search(pattern, query_lower)
        if match:
            parsed_data['spending'][category] = float(match.group(1))
        else:
            # Also try matching cases like "20000 online shopping" without "on/for"
            pattern_direct = rf"(\d+)\s*{re.escape(keyword.replace(' ', '_'))}" # Use category name for single word match
            match_direct = re.search(pattern_direct, query_lower)
            if match_direct and match_direct.start(1) < query_lower.find(keyword): # Ensure number comes before keyword
                parsed_data['spending'][category] = float(match_direct.group(1))


    # Parse reward preference
    if 'cashback' in query_lower:
        parsed_data['reward_preference'] = 'cashback'
    elif 'reward points' in query_lower or 'rewards' in query_lower:
        parsed_data['reward_preference'] = 'reward points'
    elif 'travel points' in query_lower or 'miles' in query_lower:
        parsed_data['reward_preference'] = 'travel points'

    # Parse category preference (from spending if available, otherwise direct keyword)
    if parsed_data['spending']:
        largest_category = None
        max_spend = -1
        for cat, amount in parsed_data['spending'].items():
            if amount > max_spend:
                max_spend = amount
                largest_category = cat
        parsed_data['category_preference'] = largest_category
    else:
        # Fallback if no specific spending provided but category mentioned directly
        category_keywords = {
            'online shopping': 'online_shopping',
            'groceries': 'groceries',
            'fuel': 'fuel',
            'travel': 'travel',
            'dining': 'dining'
        }
        for keyword, category in category_keywords.items():
            if keyword in query_lower:
                parsed_data['category_preference'] = category
                break

    # Parse perks preference (simple keyword match)
    perk_keywords = {
        'lounge access': 'lounge access',
        'lounge': 'lounge access',
        'fuel surcharge waiver': 'fuel surcharge waiver',
        'dining offers': 'dining offers',
        'amazon prime': 'amazon prime'
    }
    for keyword, perk_type in perk_keywords.items():
        if keyword in query_lower:
            parsed_data['perks_preference'] = perk_type
            break

    print(f"DEBUG: Parsed spending: {parsed_data['spending']}")
    print(f"DEBUG: Parsed income: {parsed_data['income']}")
    print(f"DEBUG: Reward preference: {parsed_data['reward_preference']}")
    print(f"DEBUG: Category preference: {parsed_data['category_preference']}")
    return parsed_data

def calculate_estimated_rewards(card_data, user_spending):
    """
    Calculates estimated rewards for a given card based on user's spending.
    Returns a dictionary with 'estimated_cashback_monthly_from_spending', 'net_rewards_first_year',
    'net_rewards_subsequent_years', and 'reasoning'.
    """
    monthly_cashback_from_spending = 0.0
    reasoning_parts = []
    card_reward_rules = json.loads(card_data.get('reward_rate', '{}'))

    # Calculate rewards from spending categories
    for category_rule in card_reward_rules.get('rewards', []):
        category_type = category_rule.get('category_type')

        # Ensure rate is float before calculation
        rate = float(category_rule.get('rate_percent', 0.0))

        if category_type == 'online_shopping' and user_spending.get('online_shopping', 0) > 0:
            monthly_spend = user_spending['online_shopping']
            cashback_from_category = (monthly_spend * rate) / 100
            monthly_cashback_from_spending += cashback_from_category
            reasoning_parts.append(f"{cashback_from_category:.2f} cashback from online_shopping ({monthly_spend:.2f} spent at {rate}%)")

        elif category_type == 'groceries' and user_spending.get('groceries', 0) > 0:
            monthly_spend = user_spending['groceries']
            cashback_from_category = (monthly_spend * rate) / 100
            monthly_cashback_from_spending += cashback_from_category
            reasoning_parts.append(f"{cashback_from_category:.2f} cashback from groceries ({monthly_spend:.2f} spent at {rate}%)")

        elif category_type == 'fuel' and user_spending.get('fuel', 0) > 0:
            monthly_spend = user_spending['fuel']
            cashback_from_category = (monthly_spend * rate) / 100
            monthly_cashback_from_spending += cashback_from_category
            reasoning_parts.append(f"{cashback_from_category:.2f} cashback from fuel ({monthly_spend:.2f} spent at {rate}%)")

        elif category_type == 'dining' and user_spending.get('dining', 0) > 0:
            monthly_spend = user_spending['dining']
            cashback_from_category = (monthly_spend * rate) / 100
            monthly_cashback_from_spending += cashback_from_category
            reasoning_parts.append(f"{cashback_from_category:.2f} cashback from dining ({monthly_spend:.2f} spent at {rate}%)")
        
        elif category_type == 'travel' and user_spending.get('travel', 0) > 0:
            monthly_spend = user_spending['travel']
            cashback_from_category = (monthly_spend * rate) / 100
            monthly_cashback_from_spending += cashback_from_category
            reasoning_parts.append(f"{cashback_from_category:.2f} cashback from travel ({monthly_spend:.2f} spent at {rate}%)")

        elif category_type == 'specific_merchants' and user_spending.get('online_shopping', 0) > 0:
            merchants = category_rule.get('merchants', [])
            if "amazon.in" in [m.lower() for m in merchants]:
                monthly_spend = user_spending['online_shopping']
                condition = category_rule.get('condition', '')
                cashback_from_category = (monthly_spend * rate) / 100
                monthly_cashback_from_spending += cashback_from_category
                reasoning_parts.append(f"{cashback_from_category:.2f} cashback from specific merchants (e.g., Amazon) ({monthly_spend:.2f} spent at {rate}% {condition})")
        
        elif category_type == 'all_other_spends':
            # Sum up all spending not explicitly covered by other rules
            total_user_spending = sum(user_spending.values())
            covered_spending = 0
            for r in card_reward_rules.get('rewards', []):
                if r.get('category_type') != 'all_other_spends':
                    # Need to check if a specific spending category from user_spending matches a rule's category
                    # This logic needs to be robust to prevent double counting
                    # A simpler approach for now is to subtract known spending
                    for k, v in user_spending.items():
                        if k == r.get('category_type') or \
                           (k == 'online_shopping' and r.get('category_type') == 'specific_merchants'):
                            covered_spending += v # This might overcount if multiple specific_merchants rules
            
            # This 'all_other_spends' calculation needs careful consideration to not double-count
            # For simplicity, let's assume `uncovered_spend` is total - sum of explicitly covered.
            # A more robust solution would be to track remaining spend.
            
            # Let's simplify and make sure all_other_spends calculation is correct
            # For this example, let's just make sure the rate is float
            uncovered_spend = total_user_spending - covered_spending # This logic might need refinement for complex rules
            if uncovered_spend > 0:
                cashback_from_category = (uncovered_spend * rate) / 100
                monthly_cashback_from_spending += cashback_from_category
                reasoning_parts.append(f"{cashback_from_category:.2f} cashback from all other spends ({uncovered_spend:.2f} spent at {rate}%)")


    # Apply monthly cap if specified in card rules
    max_cashback_per_month = card_reward_rules.get('max_cashback_per_month')
    if max_cashback_per_month is not None and monthly_cashback_from_spending > float(max_cashback_per_month):
        monthly_cashback_from_spending = float(max_cashback_per_month)
        reasoning_parts.append(f"Monthly spending rewards capped at card's monthly limit of {max_cashback_per_month:.2f}.")

    annual_cashback_from_spending = monthly_cashback_from_spending * 12

    # Ensure fees and bonus values are floats
    joining_fee = float(card_data.get('joining_fee', 0.0))
    annual_fee = float(card_data.get('annual_fee', 0.0))
    welcome_bonus = float(card_data.get('welcome_bonus_value', 0.0))

    # First year calculation
    net_rewards_first_year = (annual_cashback_from_spending + welcome_bonus) - joining_fee - annual_fee
    
    # Subsequent years calculation
    net_rewards_subsequent_years = annual_cashback_from_spending - annual_fee

    reasoning = "; ".join([p for p in reasoning_parts if p]) # Filter out empty parts
    if welcome_bonus > 0:
        reasoning += f"; Includes Welcome Bonus: +₹{welcome_bonus:.2f}"
    if joining_fee > 0:
        reasoning += f"; Deducts Joining Fee: -₹{joining_fee:.2f}"
    if annual_fee > 0:
        reasoning += f"; Deducts Annual Fee: -₹{annual_fee:.2f}"
    if not reasoning:
        reasoning = "No specific reward calculations applicable based on provided spending categories."

    return {
        'estimated_cashback_monthly_from_spending': monthly_cashback_from_spending,
        'net_rewards_first_year': net_rewards_first_year,
        'net_rewards_subsequent_years': net_rewards_subsequent_years,
        'reasoning': reasoning
    }

# --- Flask App Setup ---
app = Flask(__name__)
CORS(app) # Enable CORS for all routes

db_manager = DatabaseManager(DB_CONFIG)

@app.route('/recommend', methods=['POST'])
def recommend_cards():
    try:
        user_input_data = request.json
        user_query = user_input_data.get('query')

        if not user_query:
            return jsonify({"error": "No query provided in the request."}), 400

        parsed_query = parse_user_query(user_query)

        income = parsed_query.get('income')
        if income is None:
            # If income is not found in the query, respond as the advisor would
            return jsonify({"message": "Please tell me your monthly income so I can help you better."}), 200

        available_cards = db_manager.fetch_credit_cards_by_criteria(
            income=income,
            reward_preference=parsed_query.get('reward_preference'),
            category_preference=parsed_query.get('category_preference'),
            perks_preference=parsed_query.get('perks_preference')
        )

        filtered_cards = []
        for card in available_cards:
            print(f"DEBUG: --- Starting processing for card: {card.get('name')} ---")

            income_check = income >= card.get('min_income', 0)
            print(f"DEBUG:   Income Check (User: {income}, Card Min: {card.get('min_income', 0)}): {income_check}")

            reward_type_match = True
            if parsed_query.get('reward_preference'):
                user_pref_lower = parsed_query['reward_preference'].lower()
                card_reward_type_lower = card.get('reward_type', '').lower()
                
                if user_pref_lower == 'cashback':
                    reward_type_match = (card_reward_type_lower == 'cashback')
                elif user_pref_lower in ['reward points', 'travel points', 'air miles']: # Group similar point types
                    reward_type_match = (card_reward_type_lower in ['reward points', 'travel points', 'air miles'])
                else:
                    reward_type_match = False # If user asks for something else not explicitly matched
            print(f"DEBUG:   Reward Type Check (User: {parsed_query.get('reward_preference')}, Card: {card.get('reward_type')}): {reward_type_match}")


            category_match = False
            user_category_pref = parsed_query.get('category_preference')
            if user_category_pref:
                card_reward_rules = json.loads(card.get('reward_rate', '{}'))
                found_category = False
                for rule in card_reward_rules.get('rewards', []):
                    # Check for direct category match
                    if rule.get('category_type', '').lower() == user_category_pref.lower():
                        found_category = True
                        break
                    # Special handling for online_shopping if card has 'specific_merchants'
                    if user_category_pref == 'online_shopping' and rule.get('category_type', '').lower() == 'specific_merchants':
                        found_category = True
                        break
                category_match = found_category
            else:
                # If user didn't specify a category preference, any card is fine
                category_match = True
            print(f"DEBUG:   Category Check (User: {parsed_query.get('category_preference')}, Card: {card.get('name')}): {category_match}")


            perk_match = True # Assume true if no perk preference is given
            user_perks_pref = parsed_query.get('perks_preference')
            if user_perks_pref:
                card_perks = card.get('special_perks', '').lower()
                # Check if the card's special perks contain the user's preferred perk keyword
                if user_perks_pref.lower() not in card_perks:
                    perk_match = False
            print(f"DEBUG:   Perk Check (User: {parsed_query.get('perks_preference')}, Card: {card.get('name')}): {perk_match}")


            if income_check and reward_type_match and category_match and perk_match:
                print(f"DEBUG:   Card {card.get('name')} PASSED ALL FILTERS.")
                filtered_cards.append(card)
            else:
                print(f"DEBUG:   Card {card.get('name')} FAILED FILTERS.")


        print(f"DEBUG: Fetched {len(filtered_cards)} cards (after ALL Python-side filters).")

        # Process filtered cards to calculate rewards
        cards_with_estimated_rewards = []
        for card in filtered_cards:
            if parsed_query['spending']: # Only calculate if spending data is available
                try:
                    estimated_rewards_info = calculate_estimated_rewards(card, parsed_query['spending'])
                    card_info_for_display = {
                        'name': card.get('name'),
                        'issuer': card.get('issuer'),
                        'estimated_cashback_monthly_from_spending': estimated_rewards_info['estimated_cashback_monthly_from_spending'],
                        'net_rewards_first_year': estimated_rewards_info['net_rewards_first_year'],
                        'net_rewards_subsequent_years': estimated_rewards_info['net_rewards_subsequent_years'],
                        'reasoning': estimated_rewards_info['reasoning'],
                        'reward_type': card.get('reward_type'),
                        'affiliate_link': card.get('affiliate_link')
                    }
                    cards_with_estimated_rewards.append(card_info_for_display)
                except Exception as e:
                    print(f"DEBUG: An error occurred during card reward calculation for {card.get('name')}: {e}")
                    pass
            else: # If no spending data provided, return card without reward estimates
                cards_with_estimated_rewards.append({
                    'name': card.get('name'),
                    'issuer': card.get('issuer'),
                    'reward_type': card.get('reward_type'),
                    'special_perks': card.get('special_perks'),
                    'affiliate_link': card.get('affiliate_link'),
                    'reasoning': 'Please provide spending details for estimated rewards.'
                })


        if not cards_with_estimated_rewards:
            return jsonify({"message": "I couldn't find any cards matching your criteria. Try adjusting your preferences."}), 200

        # Sort by first year net rewards for best recommendation
        cards_with_estimated_rewards.sort(key=lambda x: x.get('net_rewards_first_year', -float('inf')), reverse=True)

        return jsonify({
            "message": "Based on your preferences and spending, here are some top credit card recommendations:",
            "recommendations": cards_with_estimated_rewards[:3] # Return top 3
        }), 200

    except Exception as e:
        print(f"ERROR: An internal server error occurred in recommend_cards endpoint: {e}")
        return jsonify({"error": "An internal server error occurred.", "details": str(e)}), 500

# This ensures the Flask app runs when you execute the script directly
if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)