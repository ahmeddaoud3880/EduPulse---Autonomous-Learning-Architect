"""
EduPulse UI - Complete with Search Method Selection
User can choose between Basic (BeautifulSoup) or Advanced (Tavily) search
"""
import streamlit as st
import json
import time
from pathlib import Path
from main import EduPulseWorkflow
from utils import logger

# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="EduPulse - Learning Architect",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.stProgress > div > div > div > div {
    background-color: #00cc66;
}
.quiz-correct {
    background-color: #d4edda;
    border-left: 4px solid #28a745;
    padding: 10px;
    margin: 5px 0;
}
.quiz-incorrect {
    background-color: #f8d7da;
    border-left: 4px solid #dc3545;
    padding: 10px;
    margin: 5px 0;
}
.api-key-box {
    background-color: #f0f2f6;
    border: 1px solid #ddd;
    border-radius: 5px;
    padding: 10px;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION (CRITICAL FOR BUTTON FIX!)
# ============================================================================
if 'curriculum_generated' not in st.session_state:
    st.session_state.curriculum_generated = False
if 'result' not in st.session_state:
    st.session_state.result = None
if 'pdf_path' not in st.session_state:
    st.session_state.pdf_path = None
if 'quiz_answers' not in st.session_state:
    st.session_state.quiz_answers = {}
if 'checked_answers' not in st.session_state:
    st.session_state.checked_answers = {}

# ============================================================================
# SIDEBAR - CONFIGURATION
# ============================================================================
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # ========================================
    # SEARCH METHOD SELECTION (NEW FEATURE!)
    # ========================================
    st.subheader("🔍 Search Method")
    
    search_method = st.radio(
        "Choose search method:",
        ["Basic Search (Free)", "Advanced Search (Tavily)"],
        help="Basic uses web scraping (BeautifulSoup), Advanced uses Tavily AI search API"
    )
    
    # API Key input if Tavily selected
    tavily_api_key = None
    if search_method == "Advanced Search (Tavily)":
        st.markdown('<div class="api-key-box">', unsafe_allow_html=True)
        st.markdown("**Tavily API Key Required**")
        
        tavily_api_key = st.text_input(
            "Enter your Tavily API key:",
            type="password",
            placeholder="tvly-xxxxxxxxxxxxx",
            help="Get your free API key at https://tavily.com"
        )
        
        if not tavily_api_key:
            st.warning("⚠️ Tavily API key required for advanced search!")
            st.markdown("👉 [Get free Tavily API key](https://tavily.com) (1000 searches/month free)")
        else:
            st.success("✅ API key entered!")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Tavily search info
        with st.expander("ℹ️ About Tavily Search"):
            st.markdown("""
**Tavily Advanced Search:**
- ✅ AI-powered search engine
- ✅ Better quality results
- ✅ More accurate resources
- ✅ Filters low-quality content
- ✅ 1000 free searches/month
            
**Perfect for:**
- Educational content discovery
- Research and academic topics
- Technical documentation
- Quality over quantity
            """)
    else:
        # Basic search info
        with st.expander("ℹ️ About Basic Search"):
            st.markdown("""
**Basic Web Scraping:**
- ✅ Completely free
- ✅ No API key needed
- ✅ Uses BeautifulSoup
- ⚠️ May have lower quality results
- ⚠️ Limited by scraping restrictions
            
**Good for:**
- Quick prototypes
- General topics
- When you don't have Tavily key
- Testing the system
            """)
    
    st.divider()
    
    # ========================================
    # MODEL SELECTION
    # ========================================
    st.subheader("🤖 Model Selection")
    
    model_name = st.selectbox(
        "Ollama Model:",
        [
            "qwen3.5:397b-cloud",
            "qwen3-coder-next:cloud",
            "qwen3.5:cloud",
            "qwen3:4b-instruct",
            "gpt-oss:120b-cloud",
            "gpt-oss:20b-cloud",
            "nemotron-3-super:cloud",
            "nemotron-3-ultra:cloud,"
            "minimax-m3:cloud",
            "minimax-m2.5:cloud",
            "gemma4:31b-cloud"
        ],
        index=0,
        help="Choose your model based on quality needs and available resources"
    )
    
    # Model guidance based on search method
    if search_method == "Advanced Search (Tavily)":
        st.info("💡 **With Tavily:** Use larger models (70B+) for best curation of search results. The search quality is already high, so focus on good analysis.")
    else:
        st.info("💡 **With Basic Search:** Consider using very large models (397B+) to compensate for lower search quality with better reasoning.")
    
    base_url = st.text_input(
        "Ollama URL:", 
        value="http://localhost:11434",
        help="URL where your Ollama server is running"
    )
    
    st.divider()
    
    # ========================================
    # UTILITIES
    # ========================================
    if st.button("🔄 Clear All & Start Fresh", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    
    # Show status if curriculum generated
    if st.session_state.curriculum_generated and st.session_state.result:
        st.success("✅ Curriculum Ready!")
        st.metric("Modules", len(st.session_state.result.get('syllabus', [])))
        
        # Download buttons
        if st.session_state.result:
            st.download_button(
                label="📥 Download JSON",
                data=json.dumps(st.session_state.result, indent=2),
                file_name=f"curriculum_{int(time.time())}.json",
                mime="application/json",
                use_container_width=True,
                key="download_json_sidebar"
            )
            
            if st.session_state.pdf_path and Path(st.session_state.pdf_path).exists():
                try:
                    with open(st.session_state.pdf_path, 'rb') as f:
                        st.download_button(
                            label="📄 Download PDF",
                            data=f.read(),
                            file_name=Path(st.session_state.pdf_path).name,
                            mime="application/pdf",
                            use_container_width=True,
                            key="download_pdf_sidebar"
                        )
                except Exception as e:
                    st.error(f"PDF error: {e}")

# ============================================================================
# MAIN TITLE
# ============================================================================
st.title("🎓 EduPulse - Autonomous Learning Architect")
st.markdown("### Transform any learning goal into a structured 5-day curriculum")

# ============================================================================
# INPUT SECTION
# ============================================================================
if not st.session_state.curriculum_generated:
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        topic = st.text_input(
            "What do you want to learn?",
            placeholder="e.g., Python programming, Circuit repair basics, Machine learning, Digital marketing fundamentals, ......",
            help="Be specific for better results",
            key="topic_input"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Check if conditions are met for generation
        can_generate = bool(topic)
        if search_method == "Advanced Search (Tavily)" and not tavily_api_key:
            can_generate = False
        
        generate_btn = st.button(
            "🚀 Generate Curriculum", 
            type="primary", 
            use_container_width=True,
            disabled=not can_generate
        )
    
    # Show requirement message
    if topic and search_method == "Advanced Search (Tavily)" and not tavily_api_key:
        st.error("🔑 Please enter your Tavily API key in the sidebar to use Advanced Search!")
    
    # Example topics
    st.markdown("**💡 Example topics:** *React fundamentals, Circuit troubleshooting, Python data science, Digital marketing basics*")
    
    # ========================================
    # GENERATION LOGIC
    # ========================================
    if generate_btn and topic:
        
        # Determine search method
        use_tavily = search_method == "Advanced Search (Tavily)"
        
        # Progress containers
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Expandable log
        with st.expander("📋 View Detailed Logs", expanded=True):
            log_container = st.empty()
            logs = []
        
        def update_progress(message, percent=None):
            """Update UI with progress"""
            timestamp = time.strftime('%H:%M:%S')
            logs.append(f"[{timestamp}] {message}")
            log_container.text("\n".join(logs[-25:]))
            
            if percent is not None:
                progress_bar.progress(int(percent) / 100)
                status_text.markdown(f"**{message}** • {percent:.0f}%")
            else:
                status_text.markdown(f"**{message}**")
        
        try:
            # Initialize workflow
            update_progress("🔧 Initializing agents...", 0)
            workflow = EduPulseWorkflow(
                model_name=model_name,
                base_url=base_url,
                search_method="tavily" if use_tavily else "basic",
                tavily_api_key=tavily_api_key if use_tavily else None
            )
            
            # Run workflow
            result = workflow.run(topic, progress_callback=update_progress)
            
            # Generate PDF
            if not result.get('error'):
                update_progress("📄 Generating PDF document...", 95)
                pdf_path = workflow.generate_pdf(result, topic)
                st.session_state.pdf_path = pdf_path
            
            # Store in session state
            st.session_state.result = result
            st.session_state.curriculum_generated = True
            
            # Clear progress
            progress_bar.empty()
            status_text.empty()
            
            # Success and rerun
            st.success("✅ Curriculum generated successfully!")
            time.sleep(1)
            st.rerun()
            
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"❌ An error occurred: {e}")
            logger.error(f"UI Error: {e}")
            
            with st.expander("🐛 Error Details", expanded=True):
                st.exception(e)

# ============================================================================
# RESULTS DISPLAY
# ============================================================================
else:
    result = st.session_state.result
    
    # Check if result is None
    if result is None:
        st.warning("⚠️ No curriculum generated yet. Generate one in the form above!")
        st.stop()
    
    # Check for errors
    if "error" in result:
        st.error(f"❌ {result['error']}")
        if st.button("🔄 Try Again"):
            st.session_state.curriculum_generated = False
            st.rerun()
        st.stop()
    
    # ========================================
    # Metadata Display
    # ========================================
    meta = result.get("metadata", {})
    
    st.success("✅ Your personalized learning path is ready!")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📚 Modules", meta.get("total_modules", 0))
    with col2:
        st.metric("📖 Resources", meta.get("total_resources", 0))
    with col3:
        st.metric("📝 Quiz Questions", sum(len(q['quiz']) for q in result.get('all_quizzes', [])))
    with col4:
        st.metric("⏱️ Generated in", f"{meta.get('execution_time_seconds', 0):.1f}s")
    
    st.divider()
    
    # ========================================
    # Curriculum Display
    # ========================================
    st.subheader("📋 Your 5-Day Learning Curriculum")
    
    # Tab navigation
    tab_labels = [f"Day {i+1}" for i in range(len(result['syllabus']))]
    tabs = st.tabs(tab_labels)
    
    for i, (tab, module) in enumerate(zip(tabs, result['syllabus'])):
        with tab:
            st.markdown(f"## {module['title']}")
            
            # Objective
            st.markdown("### 🎯 Learning Objective")
            st.info(module['objective'])
            
            st.divider()
            
            # Resources
            st.markdown("### 📚 Recommended Resources")
            res_entry = result["all_resources"][i]
            st.markdown(res_entry['resources'])
            
            st.divider()
            
            # Quiz
            st.markdown("### 📝 Knowledge Check")
            quiz_entry = result["all_quizzes"][i]
            
            if quiz_entry['quiz']:
                for j, q in enumerate(quiz_entry['quiz']):
                    # Unique question ID
                    question_id = f"module_{i}_q_{j}"
                    
                    st.markdown(f"**Question {j+1}:** {q['question']}")
                    
                    # Radio button for options (FIXED: unique key per question)
                    selected = st.radio(
                        "Select your answer:",
                        q['options'],
                        key=f"radio_{question_id}",
                        label_visibility="collapsed",
                        index=None  # No default selection
                    )
                    
                    # Check button (FIXED: unique key and proper state management)
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        check_clicked = st.button(
                            "✅ Check Answer",
                            key=f"btn_{question_id}",
                            disabled=(selected is None)
                        )
                    
                    # Store answer when button clicked
                    if check_clicked and selected:
                        st.session_state.checked_answers[question_id] = selected
                    
                    # Display result if answer has been checked
                    if question_id in st.session_state.checked_answers:
                        user_answer = st.session_state.checked_answers[question_id]
                        correct_answer = q['answer']
                        explanation = q.get('explanation', '')
                        
                        if user_answer == correct_answer:
                            st.markdown(
                                f"<div class='quiz-correct'>✅ <b>Correct!</b><br>{explanation}</div>",
                                unsafe_allow_html=True
                            )
                        else:
                            st.markdown(
                                f"<div class='quiz-incorrect'>❌ <b>Incorrect.</b> The correct answer is: <b>{correct_answer}</b><br>{explanation}</div>",
                                unsafe_allow_html=True
                            )
                    
                    st.markdown("")  # Spacing
            else:
                st.warning("No quiz available for this module.")
    
    st.divider()
    
    # ========================================
    # Actions
    # ========================================
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Generate New Curriculum", use_container_width=True):
            st.session_state.curriculum_generated = False
            st.session_state.quiz_answers = {}
            st.session_state.checked_answers = {}
            st.rerun()
    
    with col2:
        if st.button("📊 View Raw JSON", use_container_width=True):
            st.json(result)
    
    with col3:
        if st.session_state.pdf_path:
            st.success("PDF ready in sidebar! ↖️")
        else:
            st.info("PDF generation skipped")

# ============================================================================
# FOOTER
# ============================================================================
st.divider()
st.caption("🎓 Built with EduPulse MAS | Powered by LangChain, Ollama & Tavily | Made with Ahmed Dawod")
st.caption("💡 Tip: Choose search method in sidebar. Advanced (Tavily) provides better quality but need API key, Basic is free!")
