import logging
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

logger = logging.getLogger(__name__)


# --------------------------------------------------
# Escalation fallback
# --------------------------------------------------
def trigger_email_escalation(dispatcher: CollectingDispatcher):
    dispatcher.utter_message(response="utter_email_escalation")
    return []


# --------------------------------------------------
# Entity + Top-Intent Based Multi-Intent Handler
# --------------------------------------------------
class ActionHandleMultiIntent(Action):

    def name(self) -> Text:
        return "action_handle_multi_intent"

    # Map intents to expected entities
    INTENT_ENTITY_MAP = {
        "ask_admission_eligibility": ["qualification", "course_level", "employment_status"],
        "ask_admission_process": ["program_name"],
        "ask_course_fee": ["payment_type"],
        "ask_batch_schedule": ["batch_timing", "date_time"],
        "ask_course_info": ["course_name", "program_name", "course_level"],
        "ask_location_mode": ["study_mode", "location"],
        "ask_exam_format": ["exam_type"],
        "ask_exam_process": ["exam_type_process"],
        "ask_exam_result": ["exam_result"],
        "ask_selection_process": ["selection_criteria", "participant_status"],
        "ask_recommendation": ["recommendation_type"],
        "ask_seat_availability": ["seat_status"],
        "ask_career_guidance": ["course_name", "employment_status"],
        "ask_contact": ["organization"],
    }

    # Optional priority to resolve overlaps
    INTENT_PRIORITY = [
        "ask_admission_eligibility",
        "ask_admission_process",
        "ask_course_fee",
        "ask_batch_schedule",
        "ask_course_info",
        "ask_location_mode",
        "ask_exam_format",
        "ask_exam_process",
        "ask_exam_result",
        "ask_selection_process",
        "ask_recommendation",
        "ask_seat_availability",
        "ask_career_guidance",
        "ask_contact",
    ]

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        # Extract entities from the user message
        entities = tracker.latest_message.get("entities", [])
        entity_types = {e.get("entity") for e in entities}

        logger.info(f"Detected entities: {entity_types}")

        # Get top intents from NLU (excluding fallback)
        intent_ranking = tracker.latest_message.get("intent_ranking", [])
        intent_ranking = [i for i in intent_ranking if i["name"] != "nlu_fallback"]
        top_intents = [i["name"] for i in intent_ranking[:2]]  # take top 2

        # Get entity-matched intents
        entity_intents = self._match_intents(entity_types)

        # Combine top intents + entity intents, remove duplicates
        matched_intents = list(dict.fromkeys(top_intents + entity_intents))[:2]  # max 2

        if not matched_intents:
            return trigger_email_escalation(dispatcher)

        # respond to all matched intents 
        dispatcher.utter_message(text="Here’s what I found:")

        for intent in matched_intents:
            response = self._get_response_for_intent(intent)
            if response:
                dispatcher.utter_message(
                    text=f"**Regarding {self._format_intent_name(intent)}:**"
                )
                dispatcher.utter_message(response=response)

        return []

   
    def _match_intents(self, entity_types: set) -> List[str]:
        matched = []

        for intent, expected_entities in self.INTENT_ENTITY_MAP.items():
            if entity_types.intersection(expected_entities):
                matched.append(intent)

        # Apply priority
        matched.sort(
            key=lambda i: self.INTENT_PRIORITY.index(i)
            if i in self.INTENT_PRIORITY
            else len(self.INTENT_PRIORITY)
        )

        # Limit to top 2 intents
        return matched[:2]

    def _get_response_for_intent(self, intent_name: str) -> str:
        return {
            "ask_admission_eligibility": "utter_admission_eligibility",
            "ask_admission_process": "utter_admission_process",
            "ask_course_fee": "utter_course_fee",
            "ask_batch_schedule": "utter_batch_schedule",
            "ask_course_info": "utter_course_info",
            "ask_location_mode": "utter_location_mode",
            "ask_exam_format": "utter_exam_format",
            "ask_exam_process": "utter_exam_process",
            "ask_exam_result": "utter_exam_result",
            "ask_selection_process": "utter_selection_process",
            "ask_recommendation": "utter_recommendation",
            "ask_seat_availability": "utter_seat_availability",
            "ask_career_guidance": "utter_career_guidance",
            "ask_contact": "utter_contact",
        }.get(intent_name)

    def _format_intent_name(self, intent_name: str) -> str:
        """
        Convert intent name to readable text.
        Example: "ask_course_fee" -> "Course Fee"
        """
        return intent_name.replace("ask_", "").replace("_", " ").title()
