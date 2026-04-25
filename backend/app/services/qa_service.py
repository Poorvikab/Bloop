from __future__ import annotations

from langchain_groq import ChatGroq
from dotenv import load_dotenv
from core.config import DEFAULT_USER_ID
from services.vision_service import extract_text_from_image
from services.vector_store_service import VectorStoreService
from services.memory_service import maybe_store_chat_memory

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.2,
    max_tokens=512,
    timeout=30,
    max_retries=2,
)

vector_store = VectorStoreService()


SUMMARY_KEYWORDS = [
    "summarize",
    "summary",
    "explain",
    "overview",
    "chapter",
    "chapters",
    "outline",
    "table of contents",
    "sections",
    "what is this document about",
    "key points",
    "gist",
    "ELI5"
]


def _summary_retrieval_bias(question: str) -> str:
    q = question.lower()
    if any(keyword in q for keyword in ("chapter", "chapters", "outline", "table of contents", "contents")):
        return "chapter outline table of contents headings section"
    return "summary of the document"

def is_summary_question(question: str) -> bool:
    q = question.lower()
    return any(k in q for k in SUMMARY_KEYWORDS)


def extract_question_from_text(ocr_text: str) -> str:
    prompt = f"""
You are an educational assistant.

From the text below, extract the MAIN question being asked.
If multiple questions exist, pick the most relevant one.
If no clear question exists, rewrite the text into a clear question.

Return ONLY the question.

Text:
{ocr_text}

Question:
"""
    response = llm.invoke(prompt)
    return response.content.strip()


def build_llm_messages(context: list[dict], current_question: str) -> str:
    """
    Build conversation context for LLM
    
    Args:
        context: List of previous messages [{"role": "user/assistant", "content": "..."}]
        current_question: The current user question
    
    Returns:
        Formatted conversation history as string
    """
    if not context:
        return ""
    
    history = []
    for msg in context[-6:]:  # Last 6 messages for context window management
        role = msg["role"].capitalize()
        content = msg["content"]
        history.append(f"{role}: {content}")
    
    return "\n".join(history)


def build_memory_context(query: str, document_id: str | None, user_id: str) -> str:
    filters: dict[str, str] = {"user_id": user_id, "record_type": "semantic"}
    if document_id:
        filters["document_id"] = document_id

    memories = vector_store.search_text(query, limit=5, filters=filters)
    lines = []
    for memory in memories:
        payload = memory["payload"]
        content = payload.get("content") or payload.get("text")
        if content:
            lines.append(f"- {content}")
    return "\n".join(lines)


def answer_ques(
        question: str | None, 
        document_id: str | None = None,
        image_path: str | None = None,
        context: list[dict] | None = None,
        user_id: str | None = None,
) -> str:
    """
    Answer questions with optional document context and conversation history
    
    Args:
        question: User's question
        document_id: Optional document ID for RAG
        image_path: Optional image path for OCR
        context: Conversation history [{"role": "user/assistant", "content": "..."}]
    
    Returns:
        Generated answer
    """
    
    # Handle image-based questions
    if image_path:
        ocr_text = extract_text_from_image(image_path)

        if not ocr_text.strip():
            return "I could not extract any readable text from the image."

        question = extract_question_from_text(ocr_text)

    if not question or not question.strip():
        return "No valid question could be determined."
    
    is_summary = is_summary_question(question)

    # Build conversation history
    conversation_history = ""
    if context:
        conversation_history = build_llm_messages(context, question)

    memory_context = build_memory_context(question, document_id, user_id or DEFAULT_USER_ID)

    # RAG: Document-based answering
    if document_id:
        retrieval_query = _summary_retrieval_bias(question) if is_summary else question

        docs_with_score = vector_store.hybrid_search(
            retrieval_query,
            limit=12,
            candidate_limit=40,
            filters={"user_id": user_id or DEFAULT_USER_ID, "document_id": document_id, "record_type": "document_chunk"},
        )

        docs = [type("Doc", (), {"page_content": item["payload"].get("text", "")}) for item in docs_with_score]

        if not docs:
            return "I don't know."

        doc_context = "\n".join(doc.page_content for doc in docs if doc.page_content)

        # Build prompt based on summary or specific question
        if is_summary:
            mem_prefix = ""
            if memory_context:
                mem_prefix = f"Relevant memory:\n{memory_context}\n\n"
            
            prompt = f"""
You are an educational assistant.
Using ONLY the document content below, answer the user's request.
If the user asks for chapters, outline, or table of contents, return only the chapter or section headings.
Do not include `User:` or `Assistant:` labels.
Do not add information not present in the document.

{mem_prefix}Document:
{doc_context}

Task:
{question}

Answer:
"""
        else:
            # Build conversation context separately
            conv_prefix = ""
            if conversation_history:
                conv_prefix = f"Previous conversation:\n{conversation_history}\n\n"
            mem_prefix = ""
            if memory_context:
                mem_prefix = f"Relevant memory:\n{memory_context}\n\n"
            
            prompt = f"""
You are an educational assistant.
Answer the question ONLY using the context below.
If the answer is not present in the context, reply with:
"I don't know."

{mem_prefix}{conv_prefix}Context:
{doc_context}

Question:
{question}

Answer:
"""

    # No document: general question with conversation history
    else:
        if conversation_history:
            prompt = f"""
You are an educational assistant engaged in a conversation with a student.

Previous conversation:
{conversation_history}

Current question:
{question}

Provide a clear, concise, and helpful answer based on the conversation context.

Answer:
"""
        else:
            prompt = f"""
Answer the following question clearly and concisely.

Question:
{question}

Answer:
"""

    response = llm.invoke(prompt)
    answer = response.content.strip()

    maybe_store_chat_memory(
        user_id=user_id or DEFAULT_USER_ID,
        document_id=document_id,
        question=question,
        answer=answer,
        context=context or [],
    )

    return answer
