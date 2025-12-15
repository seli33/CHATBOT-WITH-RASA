# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

from typing import Text, Dict, Any, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher



class ActionHandleMultiIntent(Action):
    """Handling Multi intent"""
    
    def name(self) :
        return "action_handle_multi_intent"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict):
        
        #get ranked intent from the user message
        intent_ranking=tracker.latest_message.get("intent_ranking", [])

        responses=[]
        threshold=0.5

        for data in intent_ranking:
            intent=data['name']
            confidence=data['confidence']

            if confidence < threshold:
                continue

            if intent == "ask_fees":
                responses.append("The tuition is $5,000 per semester, lab fees $300, and application fee $50.")
            elif intent == "ask_batch_schedule":
                responses.append("The next batch starts on 1st March 2026.")
            elif intent == "ask_duration":
                responses.append("The course duration is 6 months.")
            elif intent == "ask_location_mode":
                responses.append("Classes are online and offline; you can choose the mode.")
            elif intent == "ask_course_info":
                responses.append("We offer AI, Data Science, and Web Development courses.")
            elif intent == "greet":
                responses.append("Hello! How can I help you today?")
            elif intent == "thank":
                responses.append("You're welcome!")
            elif intent == "goodbye":
                responses.append("Goodbye! Have a great day.")
            
            if responses:
                dispatcher.utter_message("\n".join(responses))
            else:
                dispatcher.utter_message("Sorry, I didn't understand that.")
        
            return []
