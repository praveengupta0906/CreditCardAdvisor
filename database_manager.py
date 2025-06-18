import mysql.connector
import os
import json

class DatabaseManager:
    """
    Manages connections and queries to the MySQL database for credit card data.
    """
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.cursor = None

    def connect(self):
        """
        Establishes a connection to the MySQL database.
        Sets cursor to return rows as dictionaries for easier access.
        """
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            # IMPORTANT: Set dictionary=True to get results as dictionaries (column_name: value)
            self.cursor = self.connection.cursor(dictionary=True)
            # print("Successfully connected to MySQL database!") # Uncomment for debugging connection
        except mysql.connector.Error as err:
            print(f"Error connecting to MySQL: {err}")
            self.connection = None
            self.cursor = None

    def disconnect(self):
        """
        Closes the database connection.
        """
        if self.connection and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
            # print("MySQL connection closed.") # Uncomment for debugging disconnection

    def fetch_all_credit_cards(self):
        """
        Fetches all credit cards from the database.

        Returns:
            list of dict: A list of all credit card dictionaries.
        """
        self.connect()
        query = "SELECT id, name, issuer, joining_fee, annual_fee, reward_type, reward_rate, eligibility_criteria, special_perks, image_url, apply_link FROM credit_cards"
        self.cursor.execute(query)
        cards = self.cursor.fetchall()
        self.disconnect()
        return cards

    def fetch_credit_cards_by_criteria(self, min_income: int = None, reward_type: str = None, special_perk: str = None, spending_category: str = None):
        """
        Fetches credit cards from the database based on specified criteria.

        Args:
            min_income (int, optional): The user's desired monthly income (e.g., 35000).
                                        Filters cards whose 'eligibility_criteria' specify a minimum income
                                        LESS THAN OR EQUAL TO the user's income.
                                        Assumes 'eligibility_criteria' stores text like "min. income: 35000/month"
                                        or "min. income: 6 Lakhs/year". This parsing logic is sensitive to the exact format.
            reward_type (str, optional): Keyword for preferred reward type (e.g., "cashback", "travel points", "miles").
                                         Searches for this keyword in the 'reward_type' column using LIKE.
            special_perk (str, optional): Keyword for a specific perk (e.g., "lounge access", "Amazon vouchers", "fuel surcharge waiver").
                                          Searches for this keyword in the 'special_perks' column using LIKE.
            spending_category (str, optional): Primary spending area (e.g., "fuel", "travel", "groceries", "dining", "online shopping").
                                             Searches for cards that explicitly mention benefits for this category
                                             within 'reward_type' or 'special_perks' columns, using keyword mapping.

        Returns:
            list of dict: A list of credit card dictionaries matching the criteria.
                          Returns an empty list if no cards match or an error occurs.
        """
        self.connect()
        query = "SELECT id, name, issuer, joining_fee, annual_fee, reward_type, reward_rate, eligibility_criteria, special_perks, image_url, apply_link FROM credit_cards WHERE 1=1"
        params = [] # This list will hold the parameters for the SQL query

        # --- Filter by Monthly Income ---
        if min_income is not None:
            # Modified parsing to handle "Rs 35,000" or "Rs 6 Lakhs" more robustly by stripping non-digits
            # and converting Lakhs to numeric value
            # This logic assumes income criteria is within 'eligibility_criteria' column
            query += " AND CAST(REPLACE(REPLACE(REPLACE(REPLACE(LOWER(eligibility_criteria), 'gross monthly income > rs ', ''), 'net monthly income rs. ', ''), 'lakhs p.a.', '00000'), ',', '') AS SIGNED) <= %s"
            params.append(min_income)

        # --- Filter by Reward Type (e.g., cashback, travel points) ---
        if reward_type:
            query += " AND reward_type LIKE %s"
            params.append(f"%{reward_type}%")

        # --- Filter by Special Perk (e.g., lounge access, fuel waiver) ---
        if special_perk:
            query += " AND special_perks LIKE %s"
            params.append(f"%{special_perk}%")

        # --- Filter by Spending Category (NEW, Smarter Logic) ---
        if spending_category:
            category_keywords = []
            lower_spending_category = spending_category.lower()

            # Map user categories to actual keywords in your database's reward_rate/special_perks
            if "online shopping" in lower_spending_category or "online" in lower_spending_category or "amazon" in lower_spending_category or "flipkart" in lower_spending_category:
                category_keywords.extend(['amazon', 'flipkart', 'online', 'e-commerce', 'digital', 'app', 'swiggy', 'zomato', 'myntra', 'bookmyshow', 'cult.fit', 'ola', 'tata cliq', 'uber'])
            if "fuel" in lower_spending_category:
                category_keywords.extend(['fuel', 'petrol', 'fuel surcharge'])
            if "groceries" in lower_spending_category:
                category_keywords.extend(['groceries', 'supermarket', 'daily needs', 'departmental stores'])
            if "dining" in lower_spending_category or "food" in lower_spending_category:
                category_keywords.extend(['dining', 'restaurant', 'food'])
            if "travel" in lower_spending_category:
                category_keywords.extend(['travel', 'flights', 'hotels', 'trains', 'tourism', 'airport', 'lounge']) # Added airport/lounge as often travel related perks

            if category_keywords:
                category_conditions = []
                # Search for keywords in both reward_rate and special_perks
                for keyword in category_keywords:
                    # Use LOWER() on column to ensure case-insensitive matching in MySQL
                    category_conditions.append(f"(LOWER(reward_rate) LIKE %s OR LOWER(special_perks) LIKE %s)")
                    params.append(f"%{keyword}%")
                    params.append(f"%{keyword}%")
                query += " AND (" + " OR ".join(category_conditions) + ")"
            # If spending_category is provided but no keywords match (e.g., very niche category),
            # the query won't add category filters, which is fine.

        try:
            # print(f"DEBUG SQL Query: {query}") # Uncomment for debugging
            # print(f"DEBUG SQL Params: {params}") # Uncomment for debugging
            self.cursor.execute(query, tuple(params))
            result = self.cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Error executing query in fetch_credit_cards_by_criteria: {err}")
            result = []
        finally:
            self.disconnect()
        return result