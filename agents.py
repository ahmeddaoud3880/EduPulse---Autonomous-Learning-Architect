"""
EduPulse Agents - Fixed with Proper Tavily Integration
Uses LangChain's TavilySearchResults directly
"""
import json
import re
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from langchain_ollama import ChatOllama
from langchain.prompts import ChatPromptTemplate
from langchain_community.tools.tavily_search import TavilySearchResults
from utils import logger, log_agent_action

class EduPulseAgents:
    def __init__(self, model_name="qwen3.5:397b-cloud", base_url="http://localhost:11434", 
                 search_method="tavily", tavily_api_key=None):
        """
        Initialize agents with configurable search method
        
        Args:
            model_name: Ollama model to use
            base_url: Ollama server URL
            search_method: "tavily" or "basic" (BeautifulSoup)
            tavily_api_key: Tavily API key (required if search_method="tavily")
        """
        self.llm = ChatOllama(
            model=model_name, 
            base_url=base_url,
        )
        logger.info(f"✅ Initialized EduPulseAgents with model: {model_name}")
        
        self.search_method = search_method
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        # Initialize Tavily if selected
        if search_method == "tavily":
            if tavily_api_key:
                os.environ["TAVILY_API_KEY"] = tavily_api_key
                self.tavily_search = TavilySearchResults(
                    max_results=5,
                    search_depth="advanced",
                    include_answer=True,
                    include_raw_content=False
                )
                logger.info("✅ Tavily search initialized (advanced mode)")
            else:
                logger.warning("⚠️ Tavily selected but no API key provided!")
                self.tavily_search = None
        else:
            self.tavily_search = None
            logger.info("✅ Using basic web search (BeautifulSoup)")

    def _normalize_response_content(self, response) -> str:
        raw_content = response.content
        if isinstance(raw_content, list):
            return " ".join(
                item if isinstance(item, str) else json.dumps(item)
                for item in raw_content
            ).strip()
        return str(raw_content).strip()

    def _extract_json_payload(self, text: str):
        """Extract a JSON array/object from model output, even with code fences or extra prose."""
        cleaned = text.strip()

        # Remove code fences if the model wraps the answer in ```json ... ```
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE | re.DOTALL)
        cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.IGNORECASE | re.DOTALL)

        # Normalize common smart quotes and remove trailing commas that break strict JSON
        cleaned = cleaned.replace("“", '"').replace("”", '"').replace("’", "'")
        cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        decoder = json.JSONDecoder()
        for i, char in enumerate(cleaned):
            if char in "[{":
                try:
                    obj, _ = decoder.raw_decode(cleaned[i:])
                    return obj
                except json.JSONDecodeError:
                    continue

        # Last resort: find the first balanced JSON block
        for i, char in enumerate(cleaned):
            if char in "[{":
                end = self._find_matching_bracket(cleaned, i)
                if end != -1:
                    candidate = cleaned[i:end + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        continue

        raise ValueError("No valid JSON found in model response")

    def _find_matching_bracket(self, text: str, start_index: int) -> int:
        """Return the matching closing bracket index for text[start_index]."""
        opens = "[{"
        closes = "]}"
        stack = []

        for i in range(start_index, len(text)):
            char = text[i]
            if char in opens:
                stack.append(char)
            elif char in closes:
                if not stack:
                    return -1
                top = stack.pop()
                if opens.index(top) != closes.index(char):
                    return -1
                if not stack:
                    return i

        return -1

    def syllabus_architect(self, topic: str, callbacks=None):
        """Agent 1: Syllabus Architect - Designs 10-module curriculum"""
        log_agent_action("Syllabus Architect", f"Designing curriculum for '{topic}'")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert Curriculum Designer.

              Break the topic into exactly 10 logical, sequential modules for a 10-day learning path.

              Output ONLY valid JSON in this exact format (no markdown, no extra text):
              [
              {{"title": "Module 1 Title", "objective": "Clear learning objective"}},
              {{"title": "Module 2 Title", "objective": "Clear learning objective"}},
              {{"title": "Module 3 Title", "objective": "Clear learning objective"}},
              {{"title": "Module 4 Title", "objective": "Clear learning objective"}},
              {{"title": "Module 5 Title", "objective": "Clear learning objective"}}
              etc...
              ]

              CRITICAL: Output ONLY the JSON array, nothing else."""),
                    ("user", "Topic: {topic}\n\nGenerate the 10-module curriculum now:")
        ])
        
        try:
            chain = prompt | self.llm
            response = chain.invoke({"topic": topic}, config={"callbacks": callbacks})
            content = self._normalize_response_content(response)
            
            # Extract JSON
            json_match = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
            if json_match:
                result = json_match.group(0)
                json.loads(result)  # Validate
                logger.info(f"✅ Syllabus generated successfully")
                return result
            
            return content
            
        except Exception as e:
            logger.error(f"❌ Syllabus Architect failed: {e}")
            return json.dumps([
                {"title": f"{topic} - Module {i+1}", "objective": "To be defined"} 
                for i in range(5)
            ])

    def resource_scout(self, module_title: str, topic: str, callbacks=None):
        """
        Agent 2: Resource Scout - Searches web and curates resources
        FIXED: Properly uses Tavily or BeautifulSoup based on selection
        """
        log_agent_action("Resource Scout", f"Finding resources for '{module_title}'")
        
        try:
            # STEP 1: Search the web
            search_query = f"{module_title} {topic} tutorial documentation examples"
            
            if self.search_method == "tavily" and self.tavily_search:
                # Use Tavily (Advanced)
                logger.info(f"🔍 Tavily search: {search_query}")
                
                try:
                    # Direct Tavily search
                    search_results = self.tavily_search.invoke(search_query)
                    logger.info(f"✅ Tavily returned {len(search_results) if isinstance(search_results, list) else 0} results")
                    
                    # Format results for LLM
                    formatted_results = []
                    for result in search_results[:5]:
                        if isinstance(result, dict):
                            formatted_results.append({
                                "title": result.get("title", result.get("content", "")[:100]),
                                "url": result.get("url", ""),
                                "snippet": result.get("content", "")[:300]
                            })
                    
                    search_results_text = json.dumps(formatted_results, indent=2)
                    
                except Exception as e:
                    logger.error(f"❌ Tavily search failed: {e}")
                    search_results_text = f"Error: {str(e)}"
                    
            else:
                # Use basic search (BeautifulSoup + Google)
                logger.info(f"🔍 Basic search: {search_query}")
                search_results_text = self._basic_search(search_query)
            
            # STEP 2: Ask LLM to curate
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an Educational Resource Curator.

                  Given search results, select and format the 5 BEST educational resources for the current module {module_title}.

                  Format as clean markdown:

                  **YouTube Videos:**
                  1. [Video Title](URL) - Brief description about the video content about 2 sentences.

                  **Documentation:**
                  1. [Doc Title](URL) - Brief description about the documentation content about 2 sentences.

                  **GitHub Repositories:**
                  1. [Repo Name](URL) - Brief description about the repository content about 2 sentences.

                  IMPORTANT: 
                  - Only use URLs from the search results and make sure they are relevant to the module topic and working properly.
                  - If no results available, say "No results found" for that category
                  - Do not make up links"""),
                
                ("user", """Module: {module_title}
                  Topic: {topic}

                  Search Results:
                  {search_results}

                  Select and format the 5 best resources or more or less based the long or hard is the current module that need more resources to be covered well or not or the current found resource the enough:""")
            ])
            
            chain = prompt | self.llm
            future = self.executor.submit(
                chain.invoke,
                {
                    "module_title": module_title,
                    "topic": topic,
                    "search_results": search_results_text[:3000]
                },
                config={"callbacks": callbacks}
            )
            
            response = future.result(timeout=90)
            result = self._normalize_response_content(response)
            
            logger.info(f"✅ Curated resources for '{module_title}'")
            return result
            
        except FutureTimeoutError:
            logger.warning(f"⚠️ Resource Scout timed out for '{module_title}'")
            return f"**Resources for {module_title}**\n\n[Search timed out]"
        except Exception as e:
            logger.error(f"❌ Resource Scout failed: {e}")
            return f"**Resources for {module_title}**\n\n[Error: {str(e)[:100]}]"

    def _basic_search(self, query: str) -> str:
        """Basic search using requests + BeautifulSoup"""
        try:
            import requests
            from bs4 import BeautifulSoup
            from urllib.parse import quote
            
            # Simple Google search scraping (for demonstration)
            url = f"https://www.google.com/search?q={quote(query)}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract search results
            results = []
            for g in soup.find_all('div', class_='g')[:5]:
                title_elem = g.find('h3')
                link_elem = g.find('a')
                
                if title_elem and link_elem:
                    title = title_elem.get_text()
                    link = link_elem.get('href', '')
                    results.append({"title": title, "url": link})
            
            return json.dumps(results, indent=2) if results else "No results found"
            
        except Exception as e:
            logger.error(f"Basic search failed: {e}")
            return "Basic search unavailable"

    def assessment_officer(self, module_content: str, callbacks=None):
        """Agent 3: Assessment Officer - Generates MCQ quizzes"""
        log_agent_action("Assessment Officer", "Generating quiz")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert Quiz Generator.

             Generate exactly 10 multiple-choice questions.

             Output ONLY valid JSON (no markdown, no extra text):
             [
             {{
                 "question": "What is...?",
                 "options": ["Option A", "Option B", "Option C", "Option D"],
                 "answer": "Option B",
                 "explanation": "The answer is B because... Note: this explanation should be detailed and educational and mention which part of the module this question covers."
             }},
             {{
                 "question": "Which of the following...?",
                 "options": ["Option A", "Option B", "Option C", "Option D"],
                 "answer": "Option C",
                 "explanation": "The answer is C because... Note: this explanation should be detailed and educational and mention which part of the module this question covers."
             }},
             {{
                 "question": "How does...?",
                 "options": ["Option A", "Option B", "Option C", "Option D"],
                 "answer": "Option A",
                 "explanation": "The answer is A because... Note: this explanation should be detailed and educational and mention which part of the module this question covers."
             }}
             ]
 
             CRITICAL: Output ONLY the JSON array with "question", "options", "answer", and "explanation" fields."""),
                         ("user", """Based on this module content:
                          {module_content}
                          and make sure the questions are relevant and cover the key concepts of this current module and the questions are well-structured and hard.
                          Generate 10 MCQs with explanations:""")
        ])
        
        try:
            chain = prompt | self.llm
            response = chain.invoke(
                {"module_content": module_content[:1500]},
                config={"callbacks": callbacks}
            )
            
            content = self._normalize_response_content(response)

            try:
                quiz_data = self._extract_json_payload(content)
            except Exception:
                # Fallback: if the model still returns unusable text, use the safe default.
                raise ValueError("Unable to parse quiz JSON from model response")

            if not isinstance(quiz_data, list):
                raise ValueError("Quiz response must be a JSON array")

            # Validate structure
            for q in quiz_data:
                if not isinstance(q, dict) or 'question' not in q or 'options' not in q or 'answer' not in q:
                    raise ValueError("Invalid quiz structure")

            logger.info(f"✅ Generated {len(quiz_data)} quiz questions")
            return quiz_data
            
        except Exception as e:
            logger.error(f"❌ Assessment Officer failed: {e}")
            return [
                {
                    "question": "What is the main topic of this module?",
                    "options": ["Topic A", "Topic B", "Topic C", "Topic D"],
                    "answer": "Topic A",
                    "explanation": "This is a fallback question due to generation error."
                }
            ]

    def __del__(self):
        """Cleanup"""
        try:
            self.executor.shutdown(wait=False)
        except:
            pass
