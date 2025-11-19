from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.prompts import ChatPromptTemplate
import os
from prompts import rag_prompt 
from helper import fetch_youtube_transcript
from dotenv import load_dotenv
from llm import llm

load_dotenv()

app = Flask(__name__)
CORS(app)

parser = StrOutputParser()

embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small"
)

vector_db = Chroma(
    collection_name="sessions",
    embedding_function=embedding_model,
    persist_directory="./chroma_store"
)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100
)

context_store = {}

def create_session_retriever(session_id: str, k: int = 5):
    """Create a retriever that filters by session_id"""
    return vector_db.as_retriever(
        search_kwargs={
            "k": k,
            "filter": {"session_id": session_id}
        }
    )


def format_docs(docs):
    """Format retrieved documents into a single string"""
    return "\n\n".join([doc.page_content for doc in docs])


def create_rag_chain(session_id: str):
    """
    Create a complete RAG chain for a specific session
    
    Chain flow:
    1. Input: {"question": "user question"}
    2. Retrieve relevant docs using session_id filter
    3. Format docs into context string
    4. Pass both context and question to prompt
    5. LLM generates answer
    6. Parse output as string
    """
    retriever = create_session_retriever(session_id)
    

    rag_chain = (
        RunnableParallel(
            {
                "context": retriever | format_docs,  
                "question": RunnablePassthrough()     
            }
        )
        | rag_prompt  
        | llm                   
        | parser               
    )
    
    return rag_chain


def create_simple_rag_chain(session_id: str):
    """Simpler RAG chain implementation"""
    retriever = create_session_retriever(session_id)
    
    rag_chain = (
        {
            "context": retriever | format_docs,
            "question": lambda x: x  
        }
        | rag_prompt
        | llm
        | parser
    )
    
    return rag_chain


@app.route('/youtube', methods=['POST'])
def init_youtube():
    try:
        data = request.get_json()
        video_id = data.get('videoId')

        print("\n" + "="*60)
        print("YOUTUBE VIDEO INITIALIZED")
        print("="*60)
        print(f"Video ID: {video_id}")
        print(f"YouTube URL: https://www.youtube.com/watch?v={video_id}")
        print("="*60 + "\n")

        session_id = f"yt_{video_id}"

        transcript_text = fetch_youtube_transcript(video_id)

        if not transcript_text.strip():
            return jsonify({
                "success": False,
                "sessionId": session_id,
                "message": "Transcript not found"
            }), 400

        chunks = text_splitter.split_text(transcript_text)

        metadatas = [{
            "session_id": session_id,
            "video_id": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}"
        } for _ in chunks]

        vector_db.add_texts(texts=chunks, metadatas=metadatas)
        context_store[session_id] = {
            "type": "youtube",
            "videoId": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "initialized_at": datetime.now().isoformat()
        }

        return jsonify({
            "success": True,
            "sessionId": session_id,
            "message": "Transcript loaded, chunked, and embedded"
        }), 200

    except Exception as e:
        print(f"Error in YouTube initialization: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/page', methods=['POST'])
def init_page():
    try:
        data = request.get_json()
        page_data = data.get('pageData')
        
        print("\n" + "="*60)
        print("WEB PAGE INITIALIZED")
        print("="*60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Page Title: {page_data.get('title')}")
        print(f"Page URL: {page_data.get('url')}")
        print("="*60 + "\n")
        
        session_id = f"page_{hash(page_data.get('url'))}"
        
        content = page_data.get("content", "")
        chunks = text_splitter.split_text(content)

        metadatas = [{
            "session_id": session_id,
            "url": page_data.get('url'),
            "title": page_data.get('title')
        } for _ in chunks]

        vector_db.add_texts(texts=chunks, metadatas=metadatas)

        context_store[session_id] = {
            "type": "page",
            "pageData": page_data,
            "initialized_at": datetime.now().isoformat()
        }

        return jsonify({
            "success": True,
            "sessionId": session_id,
            "message": "Page context loaded"
        }), 200
        
    except Exception as e:
        print(f"Error in page initialization: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.get_json()
        session_id = data.get('sessionId')
        message = data.get('message')
        
        print("\n" + "="*60)
        print("NEW QUESTION")
        print("="*60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Session ID: {session_id}")
        print(f"User Message: {message}")
        print("-" * 60)
        
        context = context_store.get(session_id)
        
        if not context:
            return jsonify({
                "reply": "Sorry, I couldn't find the context for this conversation. Please reload the extension.",
                "context": "none"
            }), 404
        
        context_type = context.get('type')
        
        rag_chain = create_rag_chain(session_id)
        
        try:
            answer = rag_chain.invoke(message)
        except Exception as chain_error:
            print(f"Chain error: {str(chain_error)}")
            answer = "No relevant information was found in the provided content."

        if context_type == 'youtube':
            video_id = context.get('videoId')
            response = {
                "reply": answer,
                "context": "youtube",
                "videoId": video_id
            }
        elif context_type == 'page':
            page_data = context.get('pageData', {})
            response = {
                "reply": answer,
                "context": "page",
                "pageTitle": page_data.get('title')
            }
        else:
            response = {
                "reply": "Unknown context type",
                "context": "unknown"
            }
        
        print(f"Answer generated successfully")
        print("="*60 + "\n")
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"Error in ask endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(context_store),
        "endpoints": {
            "youtube_init": "/youtube",
            "page_init": "/page",
            "ask": "/ask"
        }
    }), 200


@app.route('/clear/<session_id>', methods=['DELETE', 'POST'])
def clear_session(session_id):
    if session_id in context_store:
        del context_store[session_id]
        #vector_db.delete(filter={"session_id": session_id})
        
        print(f"\nSession cleared: {session_id}")
        print(f"Active sessions remaining: {len(context_store)}\n")
        return jsonify({"message": "Session cleared"}), 200
    return jsonify({"message": "Session not found"}), 404


if __name__ == '__main__':
    print("\n" + "*" * 30)
    print("AI Chat Assistant Server Started")
    print("*" * 30)
    print("\nServer running on: http://localhost:5000")
    print("\nAvailable endpoints:")
    print("   • POST /youtube - Initialize YouTube context")
    print("   • POST /page - Initialize page context")
    print("   • POST /ask - Ask questions (main endpoint)")
    print("   • GET  /health - Health check")
    print("   • DELETE /clear/<session_id> - Clear session")
    print("\n" + "=" * 60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)