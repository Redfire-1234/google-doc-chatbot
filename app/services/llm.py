from groq import Groq
from typing import List, Dict, Tuple, Optional

class LLMService:
    def __init__(self, api_key: str):
        """Initialize GROQ client"""
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
    
    def check_query_clarity(self, question: str, conversation_history: List[Dict[str, str]] = None) -> Tuple[bool, Optional[str]]:
        """Check if query is clear or needs clarification"""
        
        # If there's conversation history, the query is likely clear in context
        if conversation_history and len(conversation_history) > 0:
            return True, None
        
        # Only check clarity for first question or when no context
        # Very short questions (< 10 chars) might need clarification
        if len(question.strip()) < 10:
            prompt = f"""Is this question too vague to answer without more context?

Question: "{question}"

Respond with ONLY a JSON object:
{{
    "is_clear": true/false,
    "suggested_clarification": "clarifying question if needed"
}}

Mark as clear (true) unless the question is extremely vague like "what?", "huh?", "more", etc."""

            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=150
                )
                
                import json
                result_text = response.choices[0].message.content.strip()
                result_text = result_text.replace('```json', '').replace('```', '').strip()
                result = json.loads(result_text)
                
                if not result.get("is_clear", True):
                    return False, result.get("suggested_clarification")
            except:
                pass
        
        # Default: assume query is clear
        return True, None
    
    def rephrase_query(self, question: str, conversation_history: List[Dict[str, str]]) -> str:
        """Rephrase query based on conversation context"""
        
        if not conversation_history or len(conversation_history) == 0:
            return question
        
        # Build conversation context - include more history for better understanding
        context_parts = []
        for msg in conversation_history[-6:]:  # Last 6 messages (3 exchanges)
            role = "User" if msg['role'] == 'user' else "Assistant"
            # Keep full user messages, truncate assistant messages
            content = msg['content'] if msg['role'] == 'user' else msg['content'][:200]
            context_parts.append(f"{role}: {content}")
        
        context = "\n".join(context_parts)
        
        prompt = f"""Given this conversation history, rephrase the user's latest question to be standalone and include necessary context.

CONVERSATION HISTORY:
{context}

LATEST USER QUESTION: "{question}"

TASK: Rephrase this question so it's clear even without the conversation history.

EXAMPLES:
- If user asks "proper alignment" after discussing "breathing with movement in hatha yoga", rephrase as: "What is proper alignment in breathing with movement in hatha yoga?"
- If user asks "tell me more" after discussing "Product X", rephrase as: "Tell me more about Product X"
- If user asks "benefits" after discussing "meditation", rephrase as: "What are the benefits of meditation?"
- If already clear and standalone, return the EXACT same question

RULES:
1. Include context from previous messages
2. Make it specific and searchable
3. If question is already clear, return it EXACTLY as-is
4. Keep it concise but complete
5. Return ONLY the rephrased question, nothing else

REPHRASED QUESTION:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=150
            )
            
            rephrased = response.choices[0].message.content.strip()
            # Clean up the response
            rephrased = rephrased.strip('"').strip("'").strip()
            
            # Remove any labels like "Rephrased question:" or "Answer:"
            if ":" in rephrased:
                parts = rephrased.split(":", 1)
                if len(parts) == 2 and len(parts[0].split()) < 5:
                    rephrased = parts[1].strip()
            
            # Only return rephrased if it's different and not empty
            if rephrased and len(rephrased) > 0:
                # Check if significantly different (not just punctuation changes)
                if rephrased.lower().strip('?.,! ') != question.lower().strip('?.,! '):
                    return rephrased
            
            return question
        
        except Exception as e:
            print(f"Rephrasing error: {e}")
            return question
    
    def generate_answer(
        self, 
        context_chunks: List[str], 
        question: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """Generate answer using GROQ LLM with conversation history"""
        
        # Combine context chunks
        context = "\n\n".join([f"[Document Section {i+1}]\n{chunk}" for i, chunk in enumerate(context_chunks)])
        
        # Build conversation history for prompt
        history_text = ""
        if conversation_history and len(conversation_history) > 0:
            # Include last 6 messages (3 exchanges)
            recent_history = conversation_history[-6:]
            history_text = "\n\nRECENT CONVERSATION:\n"
            for msg in recent_history:
                role = "User" if msg['role'] == 'user' else "Assistant"
                # Keep user questions full, truncate assistant responses
                if msg['role'] == 'user':
                    history_text += f"{role}: {msg['content']}\n"
                else:
                    # Only show first 200 chars of previous answers
                    content = msg['content'][:200] + "..." if len(msg['content']) > 200 else msg['content']
                    history_text += f"{role}: {content}\n"
            
            history_text += "\n(Use this conversation context to understand follow-up questions)"
        
        # Create prompt
        prompt = f"""You are a helpful AI assistant answering questions about documents.

DOCUMENT CONTENT:
{context}
{history_text}

CURRENT USER QUESTION: {question}

CRITICAL INSTRUCTIONS:
1. Answer ONLY using information from the DOCUMENT CONTENT above
2. Use the conversation history to understand context for follow-up questions
3. If the user refers to something from previous messages (like "it", "that", "the technique"), use the conversation to understand what they mean, but ANSWER from the documents
4. Include inline citations: "According to the document..." or "As mentioned in the guide..."
5. If documents don't contain the answer, say: "I don't have enough information in the provided documents to answer that question."
6. Be direct and helpful - don't ask for clarification unless absolutely necessary
7. Keep answers clear and concise

ANSWER:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a document-based Q&A assistant. You understand conversation context but only answer from provided documents. You're helpful and direct."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=600,
                top_p=0.9
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            raise Exception(f"Error generating answer: {str(e)}")