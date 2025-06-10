# ------------- Environment Setup -------------
!pip install google-adk pymupdf python-dotenv
import os
import fitz  # PyMuPDF
from google.adk.agents import LlmAgent
from google.cloud import aiplatform
from concurrent.futures import ThreadPoolExecutor

# ------------- Configuration -------------
os.environ["GOOGLE_API_KEY"] = "YOUR_API_KEY" 
aiplatform.init(project="YOUR_PROJECT_ID", location="us-central1")

# ------------- ADK Agent Setup -------------
class PDFTranslationAgent:
    def __init__(self):
        self.agent = LlmAgent(
            model="gemini-2.5-pro",
            name="pdf_translator",
            instruction="""
                Translate text while preserving:
                1. Layout markers: {HEADING}, {TABLE}, {LIST}
                2. Formatting tags: <b>, <i>, <u>
                3. Structural elements: ---SECTION---, ***COLUMN***
                Maintain exact character count when possible.
            """,
            tools=[self.pdf_tool]
        )
    
    def pdf_tool(self, text_block: dict):
        """Process text blocks with layout context"""
        return self._translate_with_layout(text_block)

    def _translate_with_layout(self, block: dict):
        prompt = f"""
            Translate this text to French preserving layout markers:
            {block['text']}
            
            Context:
            - Current font: {block['font']}
            - Block type: {block['type']}
            - Position: {block['bbox']}
            - Previous text: {block['prev_text'][-200:]}
        """
        
        response = aiplatform.Endpoint.predict(
            endpoint=f"projects/{os.environ['GOOGLE_PROJECT']}/locations/us-central1/publishers/google/models/gemini-2.5-pro",
            instances=[{"content": prompt}]
        )
        return response.predictions[0]['content']

# ------------- PDF Processor -------------
class PDFTranslator:
    def __init__(self, input_path):
        self.doc = fitz.open(input_path)
        self.agent = PDFTranslationAgent()
        
    def _process_block(self, block):
        if block[6] == 0:  # Text block
            return {
                "text": block[4],
                "bbox": block[:4],
                "font": self._get_block_font(block),
                "type": self._classify_block(block)
            }
        return None

    def _get_block_font(self, block):
        spans = self.doc[block[5]].get_text("dict")["blocks"][block[6]]["spans"]
        return spans[0]["font"] if spans else "Arial"

    def _classify_block(self, block):
        text = block[4].lower()
        if any(c.isdigit() for c in text) and len(text) < 30:
            return "LIST"
        if any(kw in text for kw in ["section", "chapter"]):
            return "HEADING"
        return "BODY"

    def translate_document(self, output_path):
        with ThreadPoolExecutor(max_workers=8) as executor:
            for page in self.doc:
                blocks = page.get_text("blocks", flags=fitz.TEXT_PRESERVE_LIGATURES)
                processed = [b for b in executor.map(self._process_block, blocks) if b]
                
                # Batch translation
                translations = self.agent.agent.batch_process(
                    inputs=processed,
                    context={"page_size": page.rect}
                )
                
                # Reconstruct page
                self._rebuild_page(page, translations)
        
        self.doc.save(output_path, deflate=True, garbage=3)

    def _rebuild_page(self, page, translations):
        page.add_redact_annot(page.rect)
        page.apply_redactions()
        
        for trans in translations:
            page.insert_htmlbox(
                trans["bbox"],
                trans["translated_text"],
                css=f"font-family: {trans['font']}; font-size: {trans['font_size']}pt"
            )

# ------------- Execution -------------
if __name__ == "__main__":
    translator = PDFTranslator("input.pdf")
    translator.translate_document("output.pdf")
