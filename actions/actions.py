# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

from typing import Text, Dict, Any, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import logging

logger = logging.getLogger(__name__)

class ActionEnhancedFallback(Action):
    """Simplified fallback - NLU handles specific intents now."""
    
    def name(self) -> Text:
        return "action_enhanced_fallback"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get user's message for logging
        user_message = tracker.latest_message.get('text', '').lower()
        logger.info(f"Fallback triggered for query: '{user_message}'")
        
        # Count recent fallbacks in this conversation
        fallback_count = self._count_recent_fallbacks(tracker)
        
        # Progressive fallback strategy
        if fallback_count == 0:
            # First fallback: Ask for rephrase
            dispatcher.utter_message(
                text="Hmm, I'm not sure I understood. Could you try rephrasing your question? "
                     "Or ask me about:\n• How to apply\n• Program duration\n• Career opportunities\n• Admission requirements"
            )
        elif fallback_count == 1:
            # Second fallback: More specific suggestions
            dispatcher.utter_message(
                text="Let me help you better! Here are specific topics I can answer:\n\n"
                     " **Application & Enrollment:**\n"
                     "• 'How do I apply for the program?'\n"
                     "• 'What is the application deadline?'\n"
                     "• 'What background do I need to join?'\n\n"
                     "**Program Details:**\n"
                     "• 'How long is the program?'\n"
                     "• 'What time are the classes?'\n"
                     "• 'Are classes recorded?'\n"
                     "• 'Do I need to do project work?'\n\n"
                     "**Career & Jobs:**\n"
                     "• 'What are AI career opportunities?'\n"
                     "• 'Is there placement support?'\n"
                     "• 'What is the AI job market in Nepal?'\n\n"
                     "**Certification:**\n"
                     "• 'Is the program accredited?'\n"
                     "• 'What certificate will I get?'\n\n"
                     "Try asking one of these questions!"
            )
        else:
            # Third+ fallback: Offer human help
            dispatcher.utter_message(
                text="I'm still having trouble understanding. Would you like me to:\n"
                     "1. Connect you with a human advisor\n"
                     "2. Email you more detailed information\n"
                     "3. Schedule a callback\n\n"
                     "Just say 'human help', 'email info', or 'schedule call'!"
            )
        
        return []
    
    def _count_recent_fallbacks(self, tracker: Tracker) -> int:
        """Count how many times fallback was triggered recently."""
        fallback_count = 0
        for event in reversed(tracker.events):
            if event.get("event") == "action" and event.get("name") == self.name():
                fallback_count += 1
            elif event.get("event") == "user":
                break
        return fallback_count