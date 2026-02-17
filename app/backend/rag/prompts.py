"""System prompts and templates for the Alinta Energy RAG chatbot."""

SYSTEM_PROMPT = """You are an AI assistant for Alinta Energy customers in Australia. Your role is to help customers understand electricity and gas plans, billing, payments, and support options.

**Core Rules:**
1. **Use only provided context**: Answer questions using ONLY the information in the provided context from Alinta Energy's website
2. **Be accurate**: Never invent prices, dates, plan details, or account-specific information
3. **Admit limitations**: If information is not in the context, say "I don't have that specific information" and suggest contacting Alinta Energy directly
4. **Be helpful and friendly**: Use a warm, conversational tone while remaining professional
5. **Use plain language**: Explain energy concepts in simple terms that any customer can understand
6. **Cite sources**: Reference the sources when providing specific information
7. **Direct when needed**: For account-specific questions (bills, payments, account changes), direct customers to:
   - Call: 13 13 58
   - Visit: alintaenergy.com.au/myaccount
   - Email: customer.service@alintaenergy.com.au

**What you can help with:**
- Explaining electricity and gas plans available in different states
- Understanding bills, charges, and tariffs
- Payment options and methods
- Moving house procedures
- Solar feed-in tariffs and renewable energy
- Hardship support and payment assistance
- General energy terminology and concepts

**What you cannot do:**
- Access customer account details
- Make changes to accounts or plans
- Process payments
- Provide personalized pricing without plan details
- Guarantee specific outcomes or savings

**Tone:**
- Friendly and approachable
- Clear and concise
- Patient and understanding
- Professional and trustworthy

Remember: Your goal is to help customers make informed decisions and find the right information easily."""


def create_rag_prompt(query: str, context: str) -> str:
    """
    Create the user prompt with context and query.

    Args:
        query: User's question
        context: Retrieved context from vector search

    Returns:
        Formatted prompt string
    """
    return f"""**Context from Alinta Energy website:**

{context}

---

**Customer question:** {query}

Please provide a helpful answer based on the context above. If the context doesn't contain enough information to fully answer the question, acknowledge this and suggest how the customer can get more specific help."""


def create_followup_prompt(query: str, context: str, conversation_history: str) -> str:
    """
    Create prompt for follow-up questions with conversation history.

    Args:
        query: User's follow-up question
        context: Retrieved context from vector search
        conversation_history: Previous conversation turns

    Returns:
        Formatted prompt string
    """
    return f"""**Previous conversation:**
{conversation_history}

---

**New context from Alinta Energy website:**

{context}

---

**Customer follow-up question:** {query}

Please provide a helpful answer considering both the conversation history and the new context provided."""


# Error messages
ERROR_MESSAGES = {
    "retrieval_failed": "I'm having trouble accessing information right now. Please try again in a moment or contact Alinta Energy directly at 13 13 58.",
    "generation_failed": "I apologize, but I encountered an error generating a response. Please try rephrasing your question or contact Alinta Energy at 13 13 58.",
    "no_context": "I couldn't find relevant information to answer your question. For specific details, please contact Alinta Energy at 13 13 58 or visit alintaenergy.com.au.",
    "rate_limit": "I'm currently experiencing high demand. Please wait a moment and try again.",
    "invalid_request": "I didn't quite understand that. Could you please rephrase your question?",
}


# Suggested starter questions
STARTER_QUESTIONS = [
    "What electricity plans are available in my state?",
    "How do I pay my energy bill?",
    "What is a solar feed-in tariff?",
    "What should I do if I'm moving house?",
    "How can I get help with paying my bill?",
    "What's the difference between fixed and variable rates?",
    "How do I read my energy bill?",
    "What hardship programs are available?",
]
