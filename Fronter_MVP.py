import streamlit as st
import arxiv
from groq import Groq
from datetime import datetime

# Initialize session state
if 'paper_summaries' not in st.session_state:
    st.session_state.paper_summaries = {}
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Construct the default API client
paper_client = arxiv.Client()

# Construct the AI Client
ai_client = Groq(
    api_key=st.secrets["GROQ_KEY"]
)

# Main app title
st.set_page_config(
    page_title="Frontier", 
    page_icon="🔬",
    layout="wide"
)

# Header section
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.title("🔬 Frontier")
    st.caption("Discover and understand the latest research with AI-powered summaries")

with col2:
    st.markdown("**Built by:** Pranau Narasimhan")
    st.markdown("**Connect:** https://www.linkedin.com/in/pranau-narasimhan-19614521a/")

with col3:
    if st.button("💌 Give Feedback"):
        st.info("Send feedback to: pranaunaras12@gmail.com")

with st.expander("🎯 How to Use This Tool", expanded=True):
    st.markdown("""
    **Perfect for:** Students, researchers, academics, or anyone curious about cutting-edge science
    
    **How it works:**
    1. **Search** - Enter a research topic. (Broader fields work best. More specific fields and searches may come in the future)
    2. **Browse** - View AI-generated summaries of the latest papers
    3. **Chat** - Ask questions about the papers you've viewed
    
    **Try these example searches:**
    - "Quantum"
    - "AI"
    - "Biology"
    """)

# User inputs
option = st.text_input("Choose your interest!", placeholder="e.g., Biology, Quantum, AI, Computer Science")

expertise = st.selectbox(
    "Choose your experience level",
    ('Beginner', 'Intermediate', 'Advanced')
)

# Sidebar
with st.sidebar:
    st.header("💬 Research Assistant")
    
    # Display chat history
    if st.session_state.chat_history:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        for message in st.session_state.chat_history:
            if message['role'] == 'user':
                st.markdown(f'''
                <div class="user-message">
                    <div>{message['content']}</div>
                    <div class="timestamp">{message['timestamp']}</div>
                </div>
                ''', unsafe_allow_html=True)
            else:
                st.markdown(f'''
                <div class="assistant-message">
                    <div>{message['content']}</div>
                    <div class="timestamp">{message['timestamp']}</div>
                </div>
                ''', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("💭 Start a conversation by asking about the papers you've viewed!")
    
    # Input form for chat
    with st.form(key='chat_form', clear_on_submit=True):
        user_question = st.text_area(
            "Ask about any paper you've viewed:",
            placeholder="What would you like to know about the papers?",
            height=80,
            key="user_input"
        )
        
        col1, col2 = st.columns([2, 1])
        with col1:
            submit_button = st.form_submit_button("Send 📤", use_container_width=True)
        with col2:
            clear_button = st.form_submit_button("Clear 🗑️", use_container_width=True)
    
    # Handle clear button
    if clear_button:
        st.session_state.chat_history = []
        st.rerun()
    
    # Handle message submission
    if submit_button and user_question.strip():
        # Check if there are papers to reference
        if not st.session_state.paper_summaries:
            error_message = "⚠️ No papers loaded yet. Please search for and view some papers first before asking questions."
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': error_message,
                'timestamp': datetime.now().strftime("%H:%M")
            })
            st.rerun()
        
        # Add user message to history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_question,
            'timestamp': datetime.now().strftime("%H:%M")
        })
        
        # Prepare context from papers
        context = ""
        paper_count = 0
        for data in st.session_state.paper_summaries.values():
            context += f"\nPaper: {data['title']}\nSummary: {data['summary']}\n---"
            paper_count += 1
        
        try:
            # Show typing indicator in main area temporarily
            with st.spinner('🤔 Research Assistant is thinking...'):
                # Build conversation messages for API (including chat history)
                conversation_messages = []
                
                # Add system context with papers
                conversation_messages.append({
                    "role": "system",
                    "content": f"""You are a research assistant helping a {expertise.lower()}-level user understand academic papers. 

                            Available Papers ({paper_count} papers):
                            {context}

                            Guidelines:
                            - Reference specific papers by title when relevant
                            - Maintain conversation context from previous messages
                            - Use analogies for complex concepts at {expertise.lower()} level
                            - Keep responses concise but informative (max 250 words)
                            - If comparing papers, highlight key differences or connections
                            - Remember what was discussed previously in this conversation"""
                })
                
                # Add recent chat history (last 10 messages to maintain context while staying within token limits)
                recent_history = st.session_state.chat_history[-11:-1] if len(st.session_state.chat_history) > 1 else []
                
                for msg in recent_history:
                    if msg['role'] == 'user':
                        conversation_messages.append({
                            "role": "user", 
                            "content": msg['content']
                        })
                    elif msg['role'] == 'assistant' and not msg['content'].startswith('⚠️') and not msg['content'].startswith('❌'):
                        conversation_messages.append({
                            "role": "assistant", 
                            "content": msg['content']
                        })
                
                # Add current user question
                conversation_messages.append({
                    "role": "user",
                    "content": user_question
                })
                
                # Make API call with full conversation context
                deeper = ai_client.chat.completions.create(
                    messages=conversation_messages,
                    model='llama-3.3-70b-versatile',
                    temperature=0.7,
                    max_tokens=400
                )
                
                # Add assistant response to history
                assistant_response = deeper.choices[0].message.content
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': assistant_response,
                    'timestamp': datetime.now().strftime("%H:%M")
                })
                
        except Exception as e:
            error_message = f"❌ Sorry, there was an error: {str(e)}"
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': error_message,
                'timestamp': datetime.now().strftime("%H:%M")
            })
        
        # Rerun to update the interface
        st.rerun()
    
    # Show stats
    if st.session_state.paper_summaries:
        st.markdown(f'<div class="chat-stats">📚 {len(st.session_state.paper_summaries)} papers loaded</div>', unsafe_allow_html=True)
        if st.session_state.chat_history:
            message_count = len([msg for msg in st.session_state.chat_history if msg['role'] == 'user'])
            st.markdown(f'<div class="chat-stats">💬 {message_count} questions asked</div>', unsafe_allow_html=True)
    else:
        st.warning("📄 Search for papers above to start chatting!")

# Main content area - Paper discovery
if option:
    st.subheader(f"🔍 Latest papers on: **{option}**")
    
    with st.container():
        search = arxiv.Search(
            query=option,
            max_results=10,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )

        results = paper_client.results(search)
        
        # Add a progress bar for loading papers
        progress_bar = st.progress(0)
        paper_count = 0
        
        try:
            papers_list = list(paper_client.results(search))
            total_papers = len(papers_list)
            
            if total_papers == 0:
                st.warning("No papers found for this search term. Try a different keyword!")
            else:
                for i, r in enumerate(papers_list):
                    paper_id = r.entry_id
                    
                    # Update progress
                    progress_bar.progress((i + 1) / total_papers)
                    
                    with st.expander(f"📄 {r.title}", expanded=False):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.title(r.title)
                            st.write(f"**Published:** {r.published.strftime('%Y-%m-%d')}")
                            st.write(f"**Authors:** {', '.join([str(author) for author in r.authors])}")
                        
                        with col2:
                            st.metric("Category", r.primary_category)
                            st.write(f"**PDF:** [View Paper]({r.pdf_url})")

                        # Generate or retrieve summary
                        if paper_id not in st.session_state.paper_summaries:
                            with st.status("Generating AI summary...", expanded=False) as status:
                                try:
                                    response = ai_client.chat.completions.create(
                                        messages=[
                                            {
                                                "role": "user",
                                                "content": f"""
                                                    Title: {r.title}
                                                    Abstract: {r.summary}
                                                    Authors: {', '.join([str(author) for author in r.authors])}
                                                    Published: {r.published}
                                                    User Expertise: {expertise}

                                                    You are a research curator helping people understand cutting-edge developments. Create a clear, digestible summary:

                                                    - **What this study tackled**: Explain the problem they were solving, using everyday analogies when helpful. If there are complex terms, explain them immediately in parentheses.

                                                    - **How they did it**: Describe their approach in simple terms. Think "they tested this by..." rather than technical jargon.

                                                    - **Key discoveries**: Present findings with specific numbers, but explain what those numbers actually mean practically. Highlight anything surprising or counterintuitive.

                                                    - **Why this matters**: Connect to real-world applications or implications a general audience would care about.

                                                    Writing Guidelines:
                                                    - Assume intelligent readers who aren't experts in this field
                                                    - Immediately explain technical terms: "ptychography (an advanced imaging technique that...)"
                                                    - Use analogies to familiar concepts for complex ideas
                                                    - Keep sentences short and clear
                                                    - Call out surprising findings as interesting
                                                    - Focus on insights that make people think "oh, that's clever!"
                                                    - Adjust complexity for {expertise.lower()} level

                                                    Keep each bullet point concise but informative.
                                                    """
                                            }
                                        ],
                                        model='llama-3.3-70b-versatile'
                                    )

                                    st.session_state.paper_summaries[paper_id] = {
                                        'title': r.title,
                                        'summary': response.choices[0].message.content,
                                        'url': r.pdf_url,
                                        'category': r.primary_category
                                    }
                                    status.update(label="Summary generated!", state="complete")
                                    
                                except Exception as e:
                                    st.error(f"Error generating summary: {str(e)}")
                                    continue

                        # Display the summary
                        if paper_id in st.session_state.paper_summaries:
                            st.markdown("### 🤖 AI Summary")
                            st.write(st.session_state.paper_summaries[paper_id]['summary'])
                
                # Remove progress bar when done
                progress_bar.empty()
                
        except Exception as e:
            st.error(f"Error fetching papers: {str(e)}")
            progress_bar.empty()

else:
    st.info("👆 Enter a research topic above to discover the latest papers!")

# Optional: Add a function to manage chat history size
def maintain_chat_history_size(max_messages=30):
    """Keep only the last max_messages in chat history"""
    if len(st.session_state.chat_history) > max_messages:
        st.session_state.chat_history = st.session_state.chat_history[-max_messages:]

# Clean up chat history if it gets too long
maintain_chat_history_size()