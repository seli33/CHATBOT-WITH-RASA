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
    """Custom fallback action that suggests topics instead of just pausing."""
    
    def name(self) -> Text:
        return "action_enhanced_fallback"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get user's message
        user_message = tracker.latest_message.get('text', '').lower()
        logger.info(f"Fallback triggered for query: '{user_message}'")
        
        # Count recent fallbacks in this conversation
        fallback_count = 0
        for event in reversed(tracker.events):
            if event.get("event") == "action" and event.get("name") == self.name():
                fallback_count += 1
            elif event.get("event") == "user":
                break
        
        # Analyze keywords in the message for better suggestions
        keyword_response = self._suggest_based_on_keywords(user_message, dispatcher)
        if keyword_response:
            return []
        
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
                     "📝 **Application & Enrollment:**\n"
                     "• 'How do I apply for the program?'\n"
                     "• 'What is the application deadline?'\n"
                     "• 'What background do I need to join?'\n\n"
                     "🎓 **Program Details:**\n"
                     "• 'How long is the program?'\n"
                     "• 'What time are the classes?'\n"
                     "• 'Are classes recorded?'\n"
                     "• 'Do I need to do project work?'\n\n"
                     "💼 **Career & Jobs:**\n"
                     "• 'What are AI career opportunities?'\n"
                     "• 'Is there placement support?'\n"
                     "• 'What is the AI job market in Nepal?'\n\n"
                     "🏆 **Certification:**\n"
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
    
    def _suggest_based_on_keywords(self, message: str, dispatcher: CollectingDispatcher) -> bool:
        """Detect keywords and give helpful responses."""
        
        # Preparation/courses queries (like your example)
        if any(word in message for word in ['preparation', 'prepare', 'before starting', 'ready', 'courses before', 'prerequisite']):
            dispatcher.utter_message(
                text="For program preparation, having basic Python and math knowledge is helpful. "
                     "The program includes all necessary foundational material, but brushing up on these could be beneficial! "
                     "We also provide preparatory resources before the program starts."
            )
            return True
        
        # Project-related queries
        elif any(word in message for word in ['project', 'practical', 'hands-on', 'apply', 'real-world']):
            dispatcher.utter_message(
                text="Yes, the program includes practical AI projects where you apply real AI concepts! "
                     "These projects count toward completion and help you build a portfolio. "
                     "You'll work on real-world AI problems throughout the 6-month program."
            )
            return True
        
        # Course/curriculum queries
        elif any(word in message for word in ['course', 'curriculum', 'syllabus', 'study', 'learn', 'topics']):
            dispatcher.utter_message(
                text="The program covers machine learning, deep learning, NLP, computer vision, and AI ethics. "
                     "All courses are included in the program curriculum with hands-on projects for each module."
            )
            return True
        
        # Duration/time queries
        elif any(word in message for word in ['duration', 'length', 'how long', 'months', 'weeks', 'time']):
            dispatcher.utter_message(
                text="The program is 6 months long with live interactive sessions, practical projects, "
                     "and hands-on learning. The exact schedule is shared after enrollment."
            )
            return True
        
        # Cost/fee queries
        elif any(word in message for word in ['cost', 'fee', 'price', 'tuition', 'payment', 'expensive']):
            dispatcher.utter_message(
                text="For detailed information about program fees, payment options, and any scholarships, "
                     "I recommend contacting our admissions team directly for the most accurate and personalized information."
            )
            return True
        
        return False