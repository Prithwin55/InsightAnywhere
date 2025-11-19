from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)

context_store = {}

@app.route('/youtube', methods=['POST'])
def init_youtube():
    try:
        data = request.get_json()
        video_id = data.get('videoId')
        
        print("\n" + "="*60)
        print("YOUTUBE VIDEO INITIALIZED")
        print("="*60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Video ID: {video_id}")
        print(f"YouTube URL: https://www.youtube.com/watch?v={video_id}")
        print("="*60 + "\n")
        
        # Store video context
        session_id = f"yt_{video_id}"
        context_store[session_id] = {
            "type": "youtube",
            "videoId": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "initialized_at": datetime.now().isoformat()
        }
        
        response = {
            "success": True,
            "sessionId": session_id,
            "message": "YouTube video context loaded"
        }
        
        return jsonify(response), 200
        
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
        print(f"Description: {page_data.get('description')}")
        print(f"\nPage Content Preview:")
        print("-" * 60)
        content = page_data.get('content', '')
        print(content[:500] + "..." if len(content) > 500 else content)
        print("="*60 + "\n")
        
        session_id = f"page_{hash(page_data.get('url'))}"
        context_store[session_id] = {
            "type": "page",
            "pageData": page_data,
            "initialized_at": datetime.now().isoformat()
        }
        
        response = {
            "success": True,
            "sessionId": session_id,
            "message": "Page context loaded"
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"Error in page initialization: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.get_json()
        session_id = data.get('sessionId')
        message = data.get('message')
        
        # Get context
        context = context_store.get(session_id, {})
        context_type = context.get('type', 'unknown')
        
        print("\n" + "="*60)
        print("NEW QUESTION")
        print("="*60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Session ID: {session_id}")
        print(f"Context Type: {context_type.upper()}")
        print(f"User Message: {message}")
        print("-" * 60)
        
        if context_type == 'youtube':
            video_id = context.get('videoId')
            print(f"Video ID: {video_id}")
            print(f"YouTube URL: {context.get('url')}")
            print("="*60 + "\n")
            
            
            response = {
                "reply": f"I received your question about the YouTube video (ID: {video_id}). Question: '{message}'. Processing video content...",
                "context": "youtube",
                "videoId": video_id
            }
            
        elif context_type == 'page':
            page_data = context.get('pageData', {})
            print(f"Page: {page_data.get('title')}")
            print(f"URL: {page_data.get('url')}")
            print("="*60 + "\n")
            
            
            response = {
                "reply": f"I received your question about '{page_data.get('title')}'. Question: '{message}'. Analyzing page content...",
                "context": "page",
                "pageTitle": page_data.get('title')
            }
            
        else:
            print("No context found for this session")
            print("="*60 + "\n")
            response = {
                "reply": "Sorry, I couldn't find the context for this conversation. Please reload the extension.",
                "context": "none"
            }
        
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
        print(f"\n Session cleared: {session_id}")
        print(f"   Active sessions remaining: {len(context_store)}\n")
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