from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()
llm = ChatOpenAI(
    model="gpt-4",
    temperature=0.1,
    max_tokens=1024,
)