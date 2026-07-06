import random
import re


class ConversationHandler:
    """Handles casual conversations and greetings in a lightweight, natural way."""

    GREETING_RESPONSES = [
        "Hello! How can I assist you today?",
        "Hey there! What can I help you with?",
        "Hi! How's it going?",
        "Greetings! What would you like to do?",
        "Hello! I am ready to help.",
    ]

    HOW_ARE_YOU_RESPONSES = [
        "I'm doing well, thank you for asking! How are you?",
        "I'm doing great, thanks! How are things with you?",
        "All good here! How are you doing?",
        "Pretty great! Thanks for checking in. What about you?",
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
        "That sounds interesting! Is there anything I can help you with?",
        "I see! Let me know if you need anything else.",
        "Cool! What else can I help you with?",
        "Got it! Anything else you'd like to know?",
        "That's great! How can I assist you?",
    ]

    IDENTITY_RESPONSES = [
        "I'm Friday, your assistant. I can help with casual conversation and everyday tasks.",
        "I'm Friday, your friendly assistant. I am here to help with conversation and simple requests.",
        "I'm Friday, your personal assistant. How can I help you today?",
    ]

    GOODBYE_RESPONSES = [
        "Goodbye! Take care.",
        "See you later!",
        "Bye for now! I’m here whenever you need me.",
        "Take care!",
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

    @staticmethod
    def handle_identity(_: str) -> str:
        """Handle identity-related questions."""
        return random.choice(ConversationHandler.IDENTITY_RESPONSES)

    @staticmethod
    def handle_goodbye(_: str) -> str:
        """Handle goodbye and farewell queries."""
        return random.choice(ConversationHandler.GOODBYE_RESPONSES)

    @staticmethod
    def handle(query: str) -> str:
        """Route casual conversation requests to the right response."""
        normalized = re.sub(r"\s+", " ", (query or "").strip().lower())
        if not normalized:
            return ConversationHandler.handle_greeting(query)

        if any(term in normalized for term in ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"]):
            return ConversationHandler.handle_greeting(query)

        if any(term in normalized for term in ["how are you", "how you doing", "how's it going", "how is it going", "how do you do", "you okay", "you alright"]):
            return ConversationHandler.handle_how_are_you(query)

        if any(term in normalized for term in ["what's up", "what up", "what you doing", "what are you doing", "what are you up to", "what you up to"]):
            return ConversationHandler.handle_what_up(query)

        if any(term in normalized for term in ["who are you", "who r you", "what is your name", "what's your name", "your name"]):
            return ConversationHandler.handle_identity(query)

        if any(term in normalized for term in ["bye", "goodbye", "see you", "talk to you later", "exit", "quit"]):
            return ConversationHandler.handle_goodbye(query)

        if any(term in normalized for term in ["thanks", "thank you", "nice", "cool", "awesome", "good job", "interesting", "that sounds good", "glad", "great", "love it"]):
            return ConversationHandler.handle_small_talk(query)

        if any(term in normalized for term in ["can you", "could you", "please", "help me", "need help"]):
            return "Absolutely. I’m here to help with whatever you need."

        return ConversationHandler.handle_small_talk(query)
