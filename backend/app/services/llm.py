"""
LLM Service - Configurable LLM (OpenAI / Gemini / Claude).

RAG Flow Step 6: Pass retrieved chunks + question to LLM for answer.
Receives ONLY the retrieved context, not the full resume.
"""

from typing import List, Optional

from app.config import get_settings


class LLMService:
    """Generate answers using retrieved context + question (RAG)."""

    SYSTEM_PROMPT = """You are a resume screening assistant. You answer questions about a candidate based ONLY on the provided resume context.

Rules:
- Answer ONLY using the given context. If the context does not contain enough information, say so.
- Do NOT invent or assume facts not in the context.
- Be concise and professional.
- If asked about skills, experience, education, etc., base your answer strictly on the context."""

    def __init__(self):
        self._settings = get_settings()
        self._provider = self._settings.llm_provider.lower()

    def generate(
        self,
        question: str,
        context_chunks: List[str],
        conversation_history: Optional[List[dict]] = None,
    ) -> str:
        """
        RAG Augmented Generation: Pass ONLY retrieved chunks + question to LLM.
        
        Args:
            question: User's question
            context_chunks: Retrieved resume chunks (NOT full resume)
            conversation_history: Previous messages for context-aware chat
        """
        context = "\n\n---\n\n".join(context_chunks) if context_chunks else "No relevant resume content found."

        user_content = f"""Resume context (retrieved sections only):

{context}

---

Question: {question}"""

        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]

        if conversation_history:
            for msg in conversation_history[-6:]:  # Last 6 for context
                role = "user" if msg.get("role") == "user" else "assistant"
                messages.append({"role": role, "content": msg.get("content", "")})

        messages.append({"role": "user", "content": user_content})

        if self._provider == "openai":
            return self._call_openai(messages)
        if self._provider == "gemini":
            return self._call_gemini(messages)
        if self._provider == "claude":
            return self._call_claude(messages)
        return f"Unknown LLM provider: {self._provider}. Set LLM_PROVIDER to openai, gemini, or claude."

    def _call_openai(self, messages: List[dict]) -> str:
        """Call OpenAI API."""
        from openai import OpenAI
        client = OpenAI(api_key=self._settings.openai_api_key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=500,
        )
        return resp.choices[0].message.content or ""

            
    def _call_gemini(self, messages: List[dict]) -> str:
        """Call Google Gemini API using the official google-genai Client."""
        from google import genai

        api_key = self._settings.gemini_api_key
        if not api_key:
            return "Error: GEMINI_API_KEY not set."

        # Build a single prompt from system + conversation for Gemini.
        system_prompt = next(
            (m["content"] for m in messages if m["role"] == "system"),
            "",
        )
        user_msgs = [m["content"] for m in messages if m["role"] != "system"]

        prompt = (
            system_prompt + "\n\n" + "\n\n".join(user_msgs)
            if system_prompt
            else "\n\n".join(user_msgs)
        )

        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={"max_output_tokens": 500},
            )

            return response.text or "No response from Gemini LLM."

        except Exception as e:
            return f"Error during Gemini LLM prediction: {e}"
            

    def _call_claude(self, messages: List[dict]) -> str:
        """Call Anthropic Claude API."""
        from anthropic import Anthropic
        client = Anthropic(api_key=self._settings.anthropic_api_key)
        system = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_msgs = [m for m in messages if m["role"] != "system"]
        resp = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            system=system,
            messages=[{"role": m["role"], "content": m["content"]} for m in user_msgs],
        )
        if resp.content and resp.content[0].type == "text":
            return resp.content[0].text
        return ""
