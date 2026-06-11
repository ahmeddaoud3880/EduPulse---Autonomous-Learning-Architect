"""
EduPulse Workflow - Fixed PDF Generation
Handles cases where search fails gracefully
"""
import json
import re
import time
from datetime import datetime
from html import escape
from pathlib import Path
from agents import EduPulseAgents
from utils import logger

class EduPulseWorkflow:
    def __init__(self, model_name="qwen3.5:397b-cloud", base_url="http://localhost",
                 search_method="tavily", tavily_api_key=None):
        """
        Initialize workflow
        
        Args:
            model_name: Ollama model to use
            base_url: Ollama server URL
            search_method: "tavily" or "basic"
            tavily_api_key: Tavily API key (if using Tavily)
        """
        self.agents = EduPulseAgents(
            model_name=model_name,
            base_url=base_url,
            search_method=search_method,
            tavily_api_key=tavily_api_key
        )
        logger.info("✅ EduPulseWorkflow initialized")

    def run(self, topic: str, callbacks=None, progress_callback=None):
        """Run the complete workflow with progress tracking"""
        start_time = time.time()
        logger.info(f"🚀 Starting EduPulse workflow for: '{topic}'")
        
        def update_progress(message, percent=None):
            """Helper to update progress"""
            if progress_callback:
                progress_callback(message, percent)
            logger.info(message)
        
        # ========================================
        # PHASE 1: Syllabus Design
        # ========================================
        update_progress("🏗️  Phase 1/3: Designing curriculum...", 10)
        
        syllabus_raw = self.agents.syllabus_architect(topic, callbacks=callbacks)
        
        try:
            # Clean and parse JSON
            clean_json = re.sub(r'```json\n?|```', '', syllabus_raw).strip()
            syllabus = json.loads(clean_json)
            
            if not isinstance(syllabus, list) or len(syllabus) == 0:
                raise ValueError("Invalid syllabus format")
            
            update_progress(f"✅ Generated {len(syllabus)} modules", 20)
            
        except Exception as e:
            logger.error(f"❌ Failed to parse syllabus: {e}")
            logger.error(f"Raw output: {syllabus_raw[:500]}")
            return {
                "syllabus": [],
                "all_resources": [],
                "all_quizzes": [],
                "error": f"Failed to generate syllabus: {e}"
            }
        
        # ========================================
        # PHASE 2 & 3: Process Each Module
        # ========================================
        all_resources = []
        all_quizzes = []
        total_modules = len(syllabus)
        
        for i, module in enumerate(syllabus):
            module_num = i + 1
            module_title = module.get("title", f"Module {module_num}")
            module_objective = module.get("objective", "No objective")
            
            # Calculate progress
            progress_percent = 20 + (module_num / total_modules * 70)
            update_progress(
                f"📚 Module {module_num}/{total_modules}: {module_title}", 
                progress_percent
            )
            
            # Find Resources
            update_progress(f"   🔍 Searching for resources...", progress_percent + 2)
            
            resources = ""  # Initialize to handle exception cases
            try:
                resources = self.agents.resource_scout(
                    module_title, 
                    topic, 
                    callbacks=callbacks
                )
                all_resources.append({
                    "module": module_title,
                    "resources": resources
                })
                update_progress(f"   ✅ Resources found", progress_percent + 5)
                
            except Exception as e:
                logger.error(f"❌ Failed to find resources for {module_title}: {e}")
                all_resources.append({
                    "module": module_title,
                    "resources": f"*Error finding resources: {str(e)[:100]}*"
                })
            
            # Generate Quiz
            update_progress(f"   📝 Generating quiz...", progress_percent + 7)
            
            try:
                quiz = self.agents.assessment_officer(
                    f"Module: {module_title}\nObjective: {module_objective}\nResources: {resources[:800]}",
                    callbacks=callbacks
                )
                all_quizzes.append({
                    "module": module_title,
                    "quiz": quiz
                })
                update_progress(f"   ✅ Quiz generated", progress_percent + 10)
                
            except Exception as e:
                logger.error(f"❌ Failed to generate quiz for {module_title}: {e}")
                all_quizzes.append({
                    "module": module_title,
                    "quiz": []
                })
        
        # ========================================
        # Complete & Save
        # ========================================
        elapsed = time.time() - start_time
        update_progress(f"💾 Saving results...", 95)
        
        result = {
            "syllabus": syllabus,
            "all_resources": all_resources,
            "all_quizzes": all_quizzes,
            "metadata": {
                "topic": topic,
                "total_modules": len(syllabus),
                "total_resources": len(all_resources),
                "total_quizzes": len(all_quizzes),
                "execution_time_seconds": round(elapsed, 2),
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        
        # Save JSON
        self._save_json(result, topic)
        
        update_progress(f"✅ Pipeline complete in {elapsed:.1f} seconds!", 100)
        
        logger.info(f"📊 Results: {len(syllabus)} modules, {len(all_resources)} resource sets, {len(all_quizzes)} quizzes")
        
        return result

    def _save_json(self, result: dict, topic: str):
        """Save results to JSON file"""
        try:
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_topic = re.sub(r'[^\w\s-]', '', topic).strip().replace(' ', '_')[:50]
            filename = f"{safe_topic}_{timestamp}.json"
            
            filepath = output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 JSON saved to: {filepath}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save JSON: {e}")

    def generate_pdf(self, result: dict, topic: str) -> str | None:
        """
        Generate PDF from results with improved error handling
        
        Args:
            result: Dictionary containing curriculum results
            topic: Learning topic
            
        Returns:
            str: Path to generated PDF file (or None if failed)
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            from reportlab.lib import colors
            
            logger.info("📄 Starting PDF generation...")
            
            def safe_text(text: str) -> str:
                if text is None:
                    return ""
                return escape(str(text), quote=True)
            
            # Create output directory
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_topic = re.sub(r'[^\w\s-]', '', topic).strip().replace(' ', '_')[:50]
            filename = f"{safe_topic}_{timestamp}.pdf"
            filepath = output_dir / filename
            
            # Create PDF
            doc = SimpleDocTemplate(str(filepath), pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1a1a2e'),
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#16213e'),
                spaceAfter=12,
                fontName='Helvetica-Bold'
            )
            
            subheading_style = ParagraphStyle(
                'CustomSubheading',
                parent=styles['Heading3'],
                fontSize=14,
                textColor=colors.HexColor('#0f3460'),
                spaceAfter=8,
                fontName='Helvetica-Bold'
            )
            
            # Title page
            story.append(Paragraph(f"<b>{topic}</b>", title_style))
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph("5-Day Learning Curriculum", styles['Heading2']))
            story.append(Spacer(1, 0.1 * inch))
            story.append(Paragraph(f"Generated by EduPulse on {result['metadata']['generated_at']}", styles['Normal']))
            story.append(Spacer(1, 0.3 * inch))
            
            # Add metadata table
            meta_data = [
                ['Total Modules', str(result['metadata']['total_modules'])],
                ['Total Resources', str(result['metadata']['total_resources'])],
                ['Total Quizzes', str(result['metadata']['total_quizzes'])],
                ['Generation Time', f"{result['metadata']['execution_time_seconds']}s"]
            ]
            
            meta_table = Table(meta_data, colWidths=[3*inch, 2*inch])
            meta_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f0f0')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.white)
            ]))
            story.append(meta_table)
            
            story.append(PageBreak())
            
            # Table of Contents
            story.append(Paragraph("<b>Table of Contents</b>", heading_style))
            for i, module in enumerate(result['syllabus'], 1):
                story.append(Paragraph(f"Day {i}: {module['title']}", styles['Normal']))
                story.append(Spacer(1, 0.05 * inch))
            story.append(PageBreak())
            
            # Each module
            for i, module in enumerate(result['syllabus'], 1):
                # Module header
                story.append(Paragraph(f"<b>Day {i}: {module['title']}</b>", title_style))
                story.append(Spacer(1, 0.2 * inch))
                
                # Objective
                story.append(Paragraph("<b>Learning Objective:</b>", heading_style))
                story.append(Paragraph(module['objective'], styles['Normal']))
                story.append(Spacer(1, 0.2 * inch))
                
                # Resources
                story.append(Paragraph("<b>Recommended Resources:</b>", heading_style))
                resources_text = result['all_resources'][i-1]['resources']
                
                # Handle markdown formatting safely for PDF
                try:
                    # Convert markdown links to plain text for PDF
                    resources_text = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1: \2', resources_text)
                    # Replace special markdown characters
                    resources_text = resources_text.replace('*', '•')
                    resources_text = resources_text.replace('#', '')
                    
                    # Split into lines and add as paragraphs
                    for line in resources_text.split('\n'):
                        if line.strip():
                            story.append(Paragraph(line.replace('<', '&lt;').replace('>', '&gt;'), styles['Normal']))
                except Exception as e:
                    logger.warning(f"Error formatting resources for PDF: {e}")
                    story.append(Paragraph("Resources available in JSON output", styles['Normal']))
                
                story.append(Spacer(1, 0.2 * inch))
                
                # Quiz
                story.append(Paragraph("<b>Knowledge Check:</b>", heading_style))
                quiz = result['all_quizzes'][i-1]['quiz']
                
                if quiz:
                    for j, q in enumerate(quiz, 1):
                        try:
                            # Question (escape HTML to prevent parsing errors)
                            question_text = q.get('question', 'Question not available')
                            # Escape HTML special characters to prevent reportlab parser errors
                            question_text = question_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
                            story.append(Paragraph(f"<b>Question {j}:</b> {question_text}", subheading_style))
                            
                            # Options
                            options = q.get('options', [])
                            for k, option in enumerate(options):
                                story.append(Paragraph(f"  {chr(65+k)}. {safe_text(option)}", styles['Normal']))
                            
                            # Answer
                            answer = q.get('answer', 'N/A')
                            story.append(Paragraph(f"<b>Answer:</b> {safe_text(answer)}", styles['Normal']))
                            
                            # Explanation
                            explanation = q.get('explanation', 'No explanation provided')
                            story.append(Paragraph(f"<i>Explanation: {safe_text(explanation)}</i>", styles['Normal']))
                            story.append(Spacer(1, 0.1 * inch))
                        except Exception as e:
                            logger.warning(f"Error formatting quiz question {j}: {e}")
                            story.append(Paragraph(f"Question {j}: [Formatting error]", styles['Normal']))
                else:
                    story.append(Paragraph("No quiz questions available for this module", styles['Normal']))
                
                # Page break between modules
                if i < len(result['syllabus']):
                    story.append(PageBreak())
            
            # Build PDF
            logger.info("📄 Building PDF document...")
            doc.build(story)
            logger.info(f"✅ PDF saved to: {filepath}")
            
            return str(filepath)
            
        except ImportError as e:
            logger.warning(f"⚠️ reportlab not installed: {e}. Install with: pip install reportlab")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to generate PDF: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

if __name__ == "__main__":
    # Quick test
    workflow = EduPulseWorkflow(search_method="basic")
    
    def print_progress(message, percent=None):
        print(f"[{percent or 0:.0f}%] {message}")
    
    result = workflow.run(
        "Python for beginners",
        progress_callback=print_progress
    )
    
    print("\n" + "="*60)
    print("RESULT:")
    print("="*60)
    print(f"Modules: {len(result.get('syllabus', []))}")
    print(f"Resources: {len(result.get('all_resources', []))}")
    print(f"Quizzes: {len(result.get('all_quizzes', []))}")
    
    # Generate PDF
    pdf_path = workflow.generate_pdf(result, "Python for beginners")
    if pdf_path:
        print(f"\n📄 PDF generated: {pdf_path}")
