"""
Conversation Memory Module for Chatbot

This module provides functionality to maintain conversation history,
allowing the chatbot to keep context between user messages.
"""

class ConversationMemory:
    def __init__(self, max_turns=10):
        """
        Initialize conversation memory with a maximum number of turns to remember
        
        Args:
            max_turns (int): Maximum number of conversation turns to store
        """
        self.conversations = {}  # Dictionary to store conversations by session_id
        self.max_turns = max_turns
    
    def add_message(self, session_id, role, message):
        """
        Add a new message to the conversation history
        
        Args:
            session_id (str): Unique identifier for the conversation
            role (str): Either 'user' or 'bot'
            message (str): Content of the message
        """
        # Initialize conversation for new session
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        # Add the message to history
        self.conversations[session_id].append({
            'role': role,
            'content': message
        })
        
        # Trim history if it exceeds max_turns
        if len(self.conversations[session_id]) > self.max_turns * 2:  # *2 because each turn has user + bot message
            # Remove oldest turn (both user and bot messages)
            self.conversations[session_id] = self.conversations[session_id][2:]
    
    def get_conversation_history(self, session_id):
        """
        Get the full conversation history for a session
        
        Args:
            session_id (str): Unique identifier for the conversation
            
        Returns:
            list: List of message dictionaries with 'role' and 'content' keys
        """
        return self.conversations.get(session_id, [])
    
    def get_conversation_context(self, session_id, max_context_turns=None):
        """
        Get a condensed conversation context suitable for sending to the LLM
        
        Args:
            session_id (str): Unique identifier for the conversation
            max_context_turns (int, optional): Maximum number of turns to include in context
            
        Returns:
            str: Formatted conversation context
        """
        history = self.get_conversation_history(session_id)
        
        # If no history or max_context_turns is 0, return empty string
        if not history or max_context_turns == 0:
            return ""
        
        # Limit the number of turns if specified
        if max_context_turns:
            # Calculate how many messages to include (2 messages per turn)
            messages_to_include = max_context_turns * 2
            history = history[-messages_to_include:]
        
        # Format the conversation context
        context = "Previous conversation:\n"
        for message in history:
            role_prefix = "User: " if message['role'] == 'user' else "Bot: "
            context += f"{role_prefix}{message['content']}\n\n"
        
        return context
    
    def clear_conversation(self, session_id):
        """
        Clear the conversation history for a specific session
        
        Args:
            session_id (str): Unique identifier for the conversation
        """
        if session_id in self.conversations:
            del self.conversations[session_id]


# Global instance for use across the application
memory = ConversationMemory(max_turns=10)
