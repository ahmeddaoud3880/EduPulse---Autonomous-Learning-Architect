# 🎓 EduPulse - latest Version

# 🎓 EduPulse - System Overview

## What EduPulse Does

**EduPulse** is an autonomous AI-powered learning curriculum architect that transforms any learning goal into a structured 5-day educational plan with modules, resources, and interactive quizzes.

### Core Functionality:
1. **Takes a learning topic** from the user (e.g., "Python programming", "Circuit repair basics")
2. **Generates a 10-day curriculum** with structured modules
3. **Finds real educational resources** for each module (videos, documentation, tutorials)
4. **Creates assessment quizzes** for knowledge verification
5. **Exports as PDF** for offline access or printing

---

## System Architecture

### Multi-Agent System
EduPulse uses **3 specialized AI agents** working together:

#### 1. **Syllabus Architect Agent**
- **Role**: Curriculum designer
- **Task**: Breaks down any topic into 10 logical learning modules
- **Output**: Structured syllabus with learning objectives for each module
- **Example**: "Python Programming" → [Basics, Functions, OOP, Web Dev, Projects]

#### 2. **Resource Scout Agent**
- **Role**: Educational content finder
- **Task**: Searches for high-quality learning resources (videos, docs, tutorials, GitHub repos)
- **Methods**: 
  - **Basic Search**: Uses BeautifulSoup web scraping (free, no API key)
  - **Advanced Search**: Uses Tavily AI search (better quality, requires free API key)
- **Output**: Curated list of educational resources per module

#### 3. **Assessment Officer Agent**
- **Role**: Educational assessment creator
- **Task**: Generates quiz questions for each module to test knowledge
- **Output**: Multiple-choice questions with explanations

### Workflow Pipeline

## 🚀 Quick Start (3 Commands)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Pull a model
ollama pull qwen3.5:397b-cloud

# 3. Run!
streamlit run ui.py
```

**That's it!** Use Basic Search (free, no API key) or Advanced Search (Tavily, requires key).

---

## 🔧 What's Fixed

### 1: Tavily Search ✅

- Created `.env` file
- Implemented `TavilySearchResults` from LangChain
- Added UI input for API key
- Proper error handling and logging

**How to use:**
```python
# Now uses LangChain's Tavily directly
from langchain_community.tools.tavily_search import TavilySearchResults

tavily_search = TavilySearchResults(max_results=5, search_depth="advanced")
results = tavily_search.invoke(query)
```

### 2: Search Method Choice ✅

- Added radio button in sidebar
- "Basic Search (Free)" - BeautifulSoup, no API key needed
- "Advanced Search (Tavily)" - Tavily API, better quality
- API key input appears when Tavily selected
- Tavily signup link provided
- Helpful tips for each method

**UI Features:**
- Search method selector
- Conditional API key input
- Info expandables explaining each method
- Model recommendations per search type

### 3: PDF Generation ✅

- Comprehensive error handling
- Safe markdown-to-text conversion
- Graceful fallbacks when resources unavailable
- Character escaping for PDF compatibility
- Always generates PDF even if search fails



---

## 📦 Complete File List

```
edupulse_final/
├── agents.py           
├── main.py             
├── ui.py               
├── tools.py            
├── utils.py            
├── requirements.txt    
├── .env                
└── README.md           
```

---

## 🎯 Two Ways To Use

### Option A: Basic Search (Free, No API Key)
```
1. Install dependencies: pip install -r requirements.txt
2. Run: streamlit run ui.py
3. Select "Basic Search (Free)" in sidebar
4. Generate curriculum
5. ✅ Works without any API key!
```

**Basic Search:**
- ✅ Free, no API key
- ✅ Uses BeautifulSoup
- ⚠️ Lower quality results
- Good for: Testing, prototypes

### Option B: Advanced Search (Tavily)
```
1. Get Tavily API key: https://tavily.com (free)
2. Edit .env file, add: TAVILY_API_KEY=tvly-xxxxx
3. Run: streamlit run ui.py
4. Select "Advanced Search (Tavily)" in sidebar
5. Enter API key in sidebar input
6. Generate curriculum
7. ✅ Better quality resources!
```

**Advanced Search:**
- ✅ AI-powered search
- ✅ Better quality
- ✅ 1000 free searches/month
- ⚠️ Requires API key
- Good for: Production, real use

---

## 🔑 Tavily API Key Setup

### Step 1: Get Key
1. Go to https://tavily.com
2. Sign up (free!)
3. Get your API key (looks like: `tvly-xxxxxxxxxx`)

### Step 2: Configure
**Method A: Via .env file**
```bash
# Edit .env file
TAVILY_API_KEY=tvly-your-actual-key-here
```

**Method B: Via UI (Easier!)**
1. Select "Advanced Search (Tavily)" in sidebar
2. Enter key in the input field that appears
3. Done!

### Step 3: Use
- Generate curriculum
- Resources will be REAL (not hallucinated!)

---

## 📊 Model Selection Guide

### Speed vs. Quality (Corrected!)

**Key Insight:** Size ≠ Speed!

**What Actually Matters:**
1. Model architecture
2. Quantization method
3. Server hardware
4. Optimization level

**Recommendation:**
- **For Quality:** Use 70B+ models
- **Test Different Models:** Find your sweet spot
- **Don't Assume:** Larger ≠ slower

### Model List (Your Choices)
```
  qwen3.5:397b-cloud
  qwen3-coder-next:cloud
  qwen3.5:cloud",
  gpt-oss:120b-cloud
  gpt-oss:20b-cloud
  nemotron-3-super:cloud
  nemotron-3-ultra:cloud
  minimax-m3:cloud
  minimax-m2.5:cloud
  gemma4:31b-cloud
```

---

## 📁 Output Files

After running, you'll find:

```
output/
├── YourTopic_20260413_143025.json    # Structured data
└── YourTopic_20260413_143025.pdf     # Professional document
```

**JSON Structure:**
```json
{
  "syllabus": [...],
  "all_resources": [...],
  "all_quizzes": [...],
  "metadata": {
    "topic": "...",
    "execution_time_seconds": 420,
    "generated_at": "2026-04-13 14:30:25"
  }
}
```

**PDF Contains:**
- Title page with metadata
- Table of contents
- Each module with:
  - Learning objective
  - Resources (with URLs)
  - Quiz questions with answers and explanations

---

## 🐛 Troubleshooting

### "Tavily search not working"
**Check:**
1. API key is in `.env` file
2. Key starts with `tvly-`
3. Selected "Advanced Search (Tavily)" in UI
4. Entered key in sidebar input field

**Fix:**
- Edit `.env`: `TAVILY_API_KEY=tvly-xxxxx`
- OR enter key in UI sidebar
- Restart Streamlit

### "PDF not generating"
**Check:**
```bash
pip install reportlab
```

**Should work now!** PDF generation has comprehensive error handling.

### "Buttons redirect to main page"
**This should be FIXED!** If it still happens:
1. Check you're using the fixed `ui.py`
2. Clear browser cache
3. Restart Streamlit: `streamlit run ui.py`

**Session state properly initialized!**

### "Resources are fake/hallucinated"
**Solutions:**
- **Option A:** Use Tavily (Advanced Search) with API key
- **Option B:** Accept lower quality with Basic Search

---

## 🎯 Next Steps

1. **Install**: `pip install -r requirements.txt`
2. **Install ollama app if you don't have it**:
3. **pull each models in the project to be able to use it**: by opening the terminal of the project and make this step to all models in the system and don't worry they are all cloud models 'they are at line 201 in this file': `ollama pull model-name` and check all models you have pulled by `ollama list`
4. **Choose Search Method**: Basic (free) or Tavily (better)
5. **Run**: `streamlit run ui.py`
6. **Test All Features**: Search, PDF, buttons
7. **Enjoy**: Working system!
