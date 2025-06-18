USE credit_card_advisor_db;

CREATE TABLE credit_cards (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    issuer VARCHAR(100) NOT NULL,
    joining_fee INT,
    annual_fee INT,
    reward_type VARCHAR(100),
    reward_rate TEXT, -- TEXT for potentially long descriptions
    eligibility_criteria TEXT, -- TEXT for potentially long descriptions
    special_perks TEXT, -- TEXT for potentially long descriptions (e.g., JSON string or comma-separated)
    image_url VARCHAR(255),
    apply_link VARCHAR(255)
);
USE credit_card_advisor_db;

INSERT INTO credit_cards (name, issuer, joining_fee, annual_fee, reward_type, reward_rate, eligibility_criteria, special_perks, image_url, apply_link) VALUES
('HDFC Bank Millennia Credit Card', 'HDFC Bank', 1000, 1000, 'Cashback', '5% cashback on Amazon, Flipkart, Myntra, Zomato, Swiggy, BookMyShow, Cult.fit, Ola, Tata CLiQ, Uber. 1% cashback on all other spending. (Max Rs. 1000 cashback per month)', 'Salaried: Gross Monthly Income > Rs 35,000; Self-Employed: ITR > Rs 6 Lakhs p.a.', 'Complimentary lounge access (4 domestic per year),Fuel surcharge waiver', 'https://example.com/hdfc_millennia.png', 'https://www.hdfcbank.com/personal/ways-to-bank/credit-cards/millennia-credit-card');

INSERT INTO credit_cards (name, issuer, joining_fee, annual_fee, reward_type, reward_rate, eligibility_criteria, special_perks, image_url, apply_link) VALUES
('SBI Card PRIME', 'SBI Card', 2999, 2999, 'Reward Points', '10 reward points per Rs 100 spent on Dining, Departmental Stores, Groceries & Movies. 2 reward points per Rs 100 on all other spends. (1 RP = Rs 0.25)', 'Salaried: Age 21-60, Net Monthly Income > Rs 30,000; Self-Employed: Age 25-65, ITR > Rs 6 Lakhs p.a.', 'Welcome e-gift voucher worth Rs 3,000 (Yatra/Pantaloons),Complimentary lounge access (4 domestic, 2 international per year),Pizza Hut e-voucher worth Rs 1,000 on annual spends of Rs 50,000,Renewal fee waiver on annual spends of Rs 3 Lakhs', 'https://example.com/sbi_prime.png', 'https://www.sbicard.com/en/personal/credit-cards/prime.page');

INSERT INTO credit_cards (name, issuer, joining_fee, annual_fee, reward_type, reward_rate, eligibility_criteria, special_perks, image_url, apply_link) VALUES
('ICICI Bank Amazon Pay Credit Card', 'ICICI Bank', 0, 0, 'Cashback', '5% for Amazon Prime members, 3% for non-Prime members on Amazon.in. 2% on Amazon Pay partner merchants. 1% on all other spends.', 'Salaried: Minimum Net Monthly Income Rs. 15,000; Self-Employed: Minimum ITR Rs. 3 Lakhs p.a.', 'No joining or annual fees,Cashback credited directly as Amazon Pay balance', 'https://example.com/icici_amazon_pay.png', 'https://www.icicibank.com/personal-banking/cards/credit-card/amazon-pay-icici-bank-credit-card');

-- YOU NEED TO ADD AT LEAST 17 MORE INSERT STATEMENTS HERE FOR OTHER CARDS
-- Remember to separate special_perks with commas or another delimiter, as it's a TEXT field.