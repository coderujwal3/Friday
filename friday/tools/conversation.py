import random


class ConversationHandler:
    """Handles casual conversations and greetings."""
    
    GREETING_RESPONSES = [
        "Hello! How can I assist you?",
        "Hey there! What can I do for you?",
        "Hi! How's it going?",
        "Greetings! How can I help?",
        "Hello! What do you need?",
    ]
    
    HOW_ARE_YOU_RESPONSES = [
        "I'm doing well, thank you for asking! How about you?",
        "I'm functioning perfectly, thanks for asking! How are things with you?",
        "All good here! How are you doing?",
        "Pretty great! Thanks for checking. What about you?",
        "I'm great! Ready to help you out.",
    ]
    
    WHAT_UP_RESPONSES = [
        "Not much, just here to help! What's on your mind?",
        "Same old, ready to assist! What do you need?",
        "All good! What can I do for you?",
        "Just here for you. What's happening?",
        "Not much! What's up with you?",
    ]
    
    SMALL_TALK_RESPONSES = [
        "That's interesting! Is there anything I can help you with?",
        "I see! Let me know if you need anything.",
        "Cool! What else can I help you with?",
        "Got it! Anything else you'd like to know?",
        "That's great! How can I assist you?",
    ]
    
    @staticmethod
    def handle_greeting(_: str) -> str:
        """Handle greeting queries."""
        return random.choice(ConversationHandler.GREETING_RESPONSES)
    
    @staticmethod
    def handle_how_are_you(_: str) -> str:
        """Handle 'how are you' queries."""
        return random.choice(ConversationHandler.HOW_ARE_YOU_RESPONSES)
    
    @staticmethod
    def handle_what_up(_: str) -> str:
        """Handle 'what's up/what you doing' queries."""
        return random.choice(ConversationHandler.WHAT_UP_RESPONSES)
    
    @staticmethod
    def handle_small_talk(_: str) -> str:
        """Handle general small talk."""
        return random.choice(ConversationHandler.SMALL_TALK_RESPONSES)
