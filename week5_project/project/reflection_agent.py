from typing import List, Sequence
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, MessageGraph
from langgraph.types import Command
from langchain_community.tools.tavily_search import TavilySearchResults
from reflection_chains import generation_chain, reflection_chain, research_chain, fact_check_chain

load_dotenv()

REFLECT = "reflect"
GENERATE = "generate"
RESEARCH = "research"
FACT_CHECK = "fact_check"
HUMAN_REVIEW = "human_review"
graph = MessageGraph()

def research_node(state):
    topic = state[-1].content
    # Use Tavily for real-time web search
    tool = TavilySearchResults(max_results=3)
    research_results = tool.invoke({"query": topic})
    # Format results into a string
    research_content = "\n".join([f"{r['title']}: {r['content'][:200]}..." for r in research_results])  # Truncate for brevity
    return state + [SystemMessage(content=f"Research on '{topic}':\n{research_content}")]

def generate_node(state):
    return generation_chain.invoke({
        "messages": state
    })

def fact_check_node(state):
    article = state[-1].content
    check = fact_check_chain.invoke({"article": article})
    return state + [HumanMessage(content=check.content)]

def human_review_node(state):
    # Display current state for review
    print("\n--- Human Review ---")
    print("Current article:", state[-3].content if len(state) > 2 else "N/A")  # Assuming article is a few messages back
    print("Fact-Check Feedback:", state[-1].content)
    user_input = input("Enter feedback (e.g., 'Approve', 'Revise: add more emojis', or leave blank to continue): ").strip()
    if user_input:
        return Command(goto=GENERATE, update={"messages": state + [HumanMessage(content=user_input)]})
    else:
        return Command(goto=REFLECT)

def reflect_node(messages):
    response = reflection_chain.invoke({
        "messages": messages
    })
    return [HumanMessage(content=response.content)]

graph.add_node(RESEARCH, research_node)
graph.add_node(GENERATE, generate_node)
graph.add_node(FACT_CHECK, fact_check_node)
graph.add_node(HUMAN_REVIEW, human_review_node)
graph.add_node(REFLECT, reflect_node)
graph.set_entry_point(RESEARCH)

def should_continue(state):
    if len(state) > 12:  # Further adjusted for human input
        return END 
    return HUMAN_REVIEW  # Route to human review instead of direct reflect

graph.add_edge(RESEARCH, GENERATE)
graph.add_edge(GENERATE, FACT_CHECK)
graph.add_edge(FACT_CHECK, HUMAN_REVIEW)
graph.add_conditional_edges(HUMAN_REVIEW, should_continue)
graph.add_edge(REFLECT, GENERATE)

app = graph.compile()

# Only run this when the script is executed directly, not when imported
if __name__ == "__main__":
    print(app.get_graph().draw_mermaid())
    app.get_graph().print_ascii()
    
    response = app.invoke(HumanMessage(content="top 10 ways to become financially independent"))
    print(response)