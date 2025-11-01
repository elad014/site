document.addEventListener('DOMContentLoaded', function() {
    const chatbotToggle = document.getElementById('chatbot-toggle');
    const chatbotWindow = document.getElementById('chatbot-window');
    const chatbotClose = document.getElementById('chatbot-close');
    const chatbotSend = document.getElementById('chatbot-send');
    const chatbotInput = document.getElementById('chatbot-input');
    const chatbotMessages = document.getElementById('chatbot-messages');

    chatbotToggle.addEventListener('click', () => {
        chatbotWindow.classList.toggle('open');
    });

    chatbotClose.addEventListener('click', () => {
        chatbotWindow.classList.remove('open');
    });

    chatbotSend.addEventListener('click', sendMessage);
    chatbotInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    function sendMessage() {
        const messageText = chatbotInput.value.trim();
        if (messageText === '') return;

        appendMessage(messageText, 'user-message');
        chatbotInput.value = '';

        fetch('/chatbot/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: messageText })
        })
        .then(response => response.json())
        .then(data => {
            if (data.response) {
                appendMessage(data.response, 'bot-message');
            } else if (data.error) {
                appendMessage('Error: ' + data.error, 'bot-message');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            appendMessage('Sorry, something went wrong.', 'bot-message');
        });
    }

    function appendMessage(text, className) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', className);
        messageElement.textContent = text;
        chatbotMessages.appendChild(messageElement);
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    }
});
