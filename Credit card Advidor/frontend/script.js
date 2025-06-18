document.addEventListener('DOMContentLoaded', () => {
    const chatWindow = document.getElementById('chat-window');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const recommendationsSummary = document.getElementById('recommendations-summary');
    const cardList = document.getElementById('card-list');
    const restartButton = document.getElementById('restart-button');

    const API_URL = 'http://127.0.0.1:5000/recommend'; // Your Flask API endpoint

    function addMessage(message, sender) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', `${sender}-message`);
        messageElement.innerHTML = message; // Use innerHTML to render bold text if needed
        chatWindow.appendChild(messageElement);
        chatWindow.scrollTop = chatWindow.scrollHeight; // Auto-scroll to latest message
    }

    async function sendQuery() {
        const query = userInput.value.trim();
        if (query === '') return;

        addMessage(query, 'user');
        userInput.value = ''; // Clear input field

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: query }),
            });

            const data = await response.json();

            if (response.ok) {
                // If there are recommendations, display them and switch to summary view
                if (data.recommendations && data.recommendations.length > 0) {
                    addMessage(data.message, 'advisor');
                    displayRecommendations(data.recommendations);
                    recommendationsSummary.style.display = 'block'; // Show summary section
                    chatWindow.style.display = 'none'; // Hide chat window
                    document.getElementById('input-area').style.display = 'none'; // Hide input
                } else {
                    // If no recommendations, or if the advisor asks for more info (like income)
                    addMessage(data.message, 'advisor');
                }
            } else {
                // Handle API errors (e.g., 400, 500)
                addMessage(`Error from advisor: ${data.error || 'Something went wrong.'}`, 'advisor');
            }
        } catch (error) {
            console.error('Error fetching recommendations:', error);
            addMessage('Error: Could not connect to the advisor. Please ensure the Flask server is running.', 'advisor');
        }
    }

    function displayRecommendations(cards) {
        cardList.innerHTML = ''; // Clear previous recommendations
        cards.forEach((card, index) => {
            const cardElement = document.createElement('div');
            cardElement.classList.add('card-recommendation');

            // Format estimated rewards to 2 decimal places
            const netRewardsFirstYear = card.net_rewards_first_year ? `₹${card.net_rewards_first_year.toFixed(2)}` : 'N/A';
            const netRewardsSubsequentYears = card.net_rewards_subsequent_years ? `₹${card.net_rewards_subsequent_years.toFixed(2)}` : 'N/A';
            
            // Generate link HTML if affiliate_link exists
            const affiliateLinkHtml = card.affiliate_link ? 
                `<p><a href="${card.affiliate_link}" target="_blank">Apply Now</a></p>` : '';

            cardElement.innerHTML = `
                <h3>${index + 1}. ${card.name} (${card.reward_type})</h3>
                <p><strong>Issuer:</strong> ${card.issuer}</p>
                <p><strong>Reward Breakdown:</strong> ${card.reasoning}</p>
                <p><strong>Estimated Net Rewards (First Year):</strong> ${netRewardsFirstYear}</p>
                <p><strong>Estimated Net Rewards (Subsequent Years):</strong> ${netRewardsSubsequentYears}</p>
                ${affiliateLinkHtml}
            `;
            cardList.appendChild(cardElement);
        });
    }

    function restartFlow() {
        chatWindow.innerHTML = '<div class="message advisor-message">Hello! I\'m your Credit Card Advisor. How can I help you find the best credit card today?</div>';
        userInput.value = '';
        recommendationsSummary.style.display = 'none';
        cardList.innerHTML = '';
        chatWindow.style.display = 'flex'; // Show chat window again
        document.getElementById('input-area').style.display = 'flex'; // Show input again
    }

    // Event Listeners
    sendButton.addEventListener('click', sendQuery);
    userInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            sendButton.click();
        }
    });
    restartButton.addEventListener('click', restartFlow);
});