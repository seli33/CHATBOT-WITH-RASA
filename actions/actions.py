from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from typing import List, Dict, Any

class ActionHandleMultiIntent(Action):
    """
    Custom action with aggressive multi-intent detection.
    """
    
    def name(self) -> str:
        return "action_handle_multi_intent"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[str, Any]) -> List[Dict]:
        
        # Get intent ranking
        intent_ranking = tracker.latest_message.get("intent_ranking", [])
        
        # Define query intents
        query_intents = {
            "ask_fees", 
            "ask_batch_schedule", 
            "ask_duration", 
            "ask_location_mode", 
            "ask_course_info"
        }
        
        # STRATEGY: Detect multi-intent based on confidence gap
        detected_intents = []
        
        if intent_ranking:
            # Always include top intent if it's a query intent
            top_intent = intent_ranking[0]
            if top_intent["name"] in query_intents and top_intent["confidence"] >= 0.25:
                detected_intents.append(top_intent["name"])
                print(f"[DEBUG] Primary: {top_intent['name']} ({top_intent['confidence']:.3f})")
            
            # Check subsequent intents
            for intent_data in intent_ranking[1:6]:  # Check top 6
                intent_name = intent_data["name"]
                confidence = intent_data["confidence"]
                
                # Add if it's a query intent, meets threshold, and not duplicate
                if (intent_name in query_intents and 
                    confidence >= 0.2 and  # Lower threshold for secondary
                    intent_name not in detected_intents):
                    
                    # Additional check: confidence should be reasonably close to top intent
                    # (within 50% of top confidence)
                    if len(detected_intents) > 0:
                        confidence_ratio = confidence / intent_ranking[0]["confidence"]
                        if confidence_ratio >= 0.35:  # At least 35% of top confidence
                            detected_intents.append(intent_name)
                            print(f"[DEBUG] Secondary: {intent_name} ({confidence:.3f})")
                    else:
                        detected_intents.append(intent_name)
                        print(f"[DEBUG] Added: {intent_name} ({confidence:.3f})")
        
        print(f"[DEBUG] Final detected intents: {detected_intents}")
        
        # Define responses
        intent_responses = {
            "ask_fees": (
                "💰 **Course Fees:**\n"
                "• Tuition: $5,000 per semester\n"
                "• Lab fees: $300\n"
                "• Application fee: $50"
            ),
            "ask_batch_schedule": (
                "📅 **Next Batch:**\n"
                "The next batch starts on **March 1st, 2026**"
            ),
            "ask_duration": (
                "⏱️ **Course Duration:**\n"
                "The course is **6 months** long (24 weeks)"
            ),
            "ask_location_mode": (
                "📍 **Class Mode:**\n"
                "We offer both **online** and **offline** classes.\n"
                "You can choose the mode that works best for you!"
            ),
            "ask_course_info": (
                "📚 **Our Courses:**\n"
                "We offer the following programs:\n"
                "• Artificial Intelligence (AI)\n"
                "• Data Science\n"
                "• Web Development"
            ),
        }
        
        # Build response
        if detected_intents:
            responses = [
                intent_responses[intent] 
                for intent in detected_intents 
                if intent in intent_responses
            ]
            
            if len(responses) > 1:
                message = "Here's the information you requested:\n\n" + "\n\n".join(responses)
            elif len(responses) == 1:
                message = responses[0]
            else:
                dispatcher.utter_message(response="utter_fallback")
                return []
            
            dispatcher.utter_message(text=message)
        else:
            dispatcher.utter_message(response="utter_fallback")
        
        return []