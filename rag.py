from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv
from rapidfuzz import fuzz, process
from collections import deque
from functools import lru_cache
import os

# Configuration
load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_PORT = os.getenv("QDRANT_PORT")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)
COLLECTION_NAME = "faq_chunks"


class RAGSystem:
    def __init__(self):
        print("Initializing RAG System...")

        # Load embedding model
        print("Loading embedding model...")
        self.embedding = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        print("Embedding model loaded")

        # Connect to Qdrant
        print("Connecting to Qdrant...")
        if QDRANT_API_KEY:
            self.client = QdrantClient(
                url=QDRANT_URL,
                api_key=QDRANT_API_KEY,
            )
        else:
            self.client = QdrantClient(
                host=QDRANT_URL,
                port=int(QDRANT_PORT),
            )

        try:
            collections = self.client.get_collections()
            print(
                f"Qdrant connected. Available collections: {[c.name for c in collections.collections]}"
            )
        except Exception as e:
            print(f"Warning: Could not verify Qdrant connection: {e}")

        print("Qdrant connected")

        # Initialize LLM
        self.llm = Ollama(
            model="qwen2.5:1.5b",
            temperature=0.1,
            num_ctx=2048,
            num_predict=200,
            num_thread=2,
        )
        # Conversation history 
        self.chat_history=deque(maxlen=5) #last 5 turns

        print("RAG System ready!\n")

    def format_chat_history(self):
        if not  self.chat_history:
            return ""
        
        text_history=[]
        for i, turn in enumerate(self.chat_history,1):
            text_history.append(
            f"Turn {i}:\n"
            f"User: {turn['user']}\n"
            f"Assistant: {turn['assistant']}\n"
        )
        return "\n".join(text_history)


    @lru_cache(maxsize=128)
    def embed_query_cached(self, query):
        return self.embedding.embed_query(query)

    def correct_query_fuzzy(self, query):
        domain_terms = ["eligibility", "eligible", "admission", "application", "fellowship", "syllabus", "curriculum",
                        "assignment", "project", "exam", "interview", "placement", "stipend", "compensation", "duration",
                        "schedule", "machine learning", "deep learning", "computer vision", "natural language processing",
                        "generative ai", "mlops", "online", "attendance", "certificate"]
        

        words = query.lower().split()
        corrected_words = []

        for word in words:
            if len(word) <= 3:
                corrected_words.append(word)
                continue

            match = process.extractOne(
                word,
                domain_terms,
                scorer=fuzz.ratio,
                score_cutoff=80,
            )

            if match:
                corrected_words.append(match[0])
            else:
                corrected_words.append(word)

        return " ".join(corrected_words)

    def retrieve_similar_chunks(self, query, top_k=3):
        query_embedding = self.embed_query_cached(query)

        search_result = self.client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_embedding,
            limit=top_k,
            with_payload=True,
        )

        search_results = search_result.points

        query_lower = query.lower()
        if any(
            word in query_lower
            for word in ["eligib", "eligible", "apply", "requirement", "criteria"]
        ):
            filtered = [
                r
                for r in search_results
                if r.payload.get("keywords")
                and "eligib" in r.payload["keywords"].lower()
            ]
            if filtered:
                search_results = filtered

        return search_results

    def format_context(self, chunks):
        context_parts = []

        for i, chunk in enumerate(chunks, 1):
            header = chunk.payload.get("header", "")
            content = chunk.payload.get("content", "")

            if "**Common Variations**:" in content:
                content = content.split("**Common Variations**:")[0]

            context_parts.append(
                f"[Document {i}]\n"
                f"Question: {header}\n"
                f"Answer:\n{content}\n"
            )

        return "\n".join(context_parts)

    def generate_answer(self, query, context):
        chat_history = self.format_chat_history()
        prompt = f"""You are a retrieval-based FAQ assistant for the AI Fellowship Program.

Previous conversation (for context only, NOT a knowledge source):
{chat_history if chat_history else "No previous conversation."}

Answer the question using ONLY the information in the provided context.

CRITICAL RULES:
- Use only the factual information present in the context
- Do NOT copy headings, labels, or formatting such as "Quick Answer" or "Details"
- Rewrite the answer as a short, clear, natural paragraph donot give long explainations but keep the context of the answer
- Use a formal and friendly tone
- Do not use outside knowledge or assumptions
- If the context does not DIRECTLY and COMPLETELY answer the question, you MUST respond with EXACTLY:
  "This information is not available in the FAQ."

Instructions:
- Answer only what is explicitly supported by the context
- If any part of the question is unsupported, return the fallback sentence
- Keep the answer concise, factual, and paraphrased
- Ignore sections labeled "Common Variations" or "Related Topics"

Context:
{context}

Question:
{query}

Answer:"""

        answer = self.llm.invoke(prompt)

        if hasattr(answer, "content"):
            answer = answer.content

        fallback_phrases = [
            "not available in the faq",
            "not available in faq",
            "cannot answer",
            "don't have",
            "no information",
            "context does not",
            "i don't know",
            "i cannot",
            "unable to answer",
        ]

        answer_lower = answer.lower()
        if any(phrase in answer_lower for phrase in fallback_phrases):
            return "This information is not available in the FAQ."

        if len(answer.strip()) < 25:
            return "This information is not available in the FAQ."

        return answer.strip()

    def query(self, question, top_k=3, show_context=False):
        corrected_question = self.correct_query_fuzzy(question)
        if corrected_question != question.lower():
            print(f"Corrected: '{question}' -> '{corrected_question}'")

        print("Question:", corrected_question, "\n")

        print("Retrieving top", top_k, "relevant chunks...")
        chunks = self.retrieve_similar_chunks(corrected_question, top_k)

        if not chunks:
            return "This information is not available in the FAQ."

        print("Found", len(chunks), "relevant chunks\n")

        if show_context:
            print("Retrieved Context:")
            print("-" * 80)
            for i, chunk in enumerate(chunks, 1):
                header = chunk.payload.get("header", "")
                keywords = chunk.payload.get("keywords", "")
                content = chunk.payload.get("content", "")
                similarity = chunk.score

                print(f"\n[Chunk {i}] (Similarity: {similarity:.3f})")
                print("Header:", header)
                print("Keywords:", keywords)
                print("Content (FULL):")
                print(content)
                print()
            print("-" * 80 + "\n")

        similarities = [chunk.score for chunk in chunks]
        max_similarity = max(similarities)

        MIN_SIMILARITY = 0.55
        if max_similarity < MIN_SIMILARITY:
            print(
                f"Max similarity {max_similarity:.3f} below threshold {MIN_SIMILARITY}"
            )
            return "This information is not available in the FAQ."

        context = self.format_context(chunks)
        answer = self.generate_answer(corrected_question, context)
        
        self.chat_history.append(
        {
            "user": corrected_question,
            "assistant": answer
        }
        )

        return answer

    def close(self):
        self.client.close()
        print("Qdrant connection closed")


if __name__ == "__main__":
    rag = RAGSystem()

    print("RAG System Interactive Mode")
    print("Type 'quit' to exit, 'context' to toggle context display\n")

    show_context = True

    while True:
        user_input = input("Ask a question: ").strip()

        if user_input.lower() == "quit":
            break

        if user_input.lower() == "context":
            show_context = not show_context
            print("Context display:", "ON" if show_context else "OFF", "\n")
            continue

        if not user_input:
            continue

        print("\nAnswer:")
        answer = rag.query(user_input, top_k=3, show_context=show_context)
        print(answer)
        print("\n" + "=" * 80 + "\n")

    rag.close()
