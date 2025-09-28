from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

generation_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a medium techie influencer assistant tasked with writing excellent Medium articles."
            " Generate the best Medium article possible for the user's request."
            " If the user provides critique, respond with a revised version of your previous attempts.",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

reflection_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a viral Medium influencer grading an article. Generate critique and recommendations for the user's article."
            "Always provide detailed recommendations, including requests for length, hooks, virality, style, etc.",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

research_prompt = ChatPromptTemplate.from_template(
    "Research the following topic and provide key facts, context, and relevant insights for creating a Medium article: {topic}"
)

fact_check_prompt = ChatPromptTemplate.from_template(
    "Fact-check the following article for accuracy, factual claims, and potential misinformation. Provide corrections or notes if needed: {article}"
)

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

generation_chain = generation_prompt | llm
reflection_chain = reflection_prompt | llm
research_chain =   research_prompt   | llm
fact_check_chain = fact_check_prompt | llm