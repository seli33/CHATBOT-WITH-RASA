from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

# Import your RAG system
from rag import RAGSystem  # make sure your RAG code is in rag_system.py

# Initialize RAG once
rag = RAGSystem()

class ActionHandleMultiIntent(Action):
    def name(self) -> Text:
        return "action_handle_multi_intent"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Dict[Text, Any]]:

        # Get latest user message
        user_message = tracker.latest_message.get("text")
        if not user_message:
            dispatcher.utter_message(text="I didn't receive any input.")
            return []

        # Query RAG for multi-intent / complex question
        answer = rag.query(user_message, top_k=3, show_context=False)

        # Return RAG answer
        dispatcher.utter_message(text=answer)

        return []

# Optional: close RAG client when Rasa shuts down
class ActionCloseRAG(Action):
    def name(self) -> Text:
        return "action_close_rag"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Dict[Text, Any]]:
        rag.close()
        return []
