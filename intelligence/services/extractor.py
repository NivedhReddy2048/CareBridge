import os
import re
import traceback
import logging
import pdfplumber
import pytesseract
from PIL import Image, ImageEnhance, ImageOps

logger = logging.getLogger(__name__)

# Configure Advanced Feature Flags
ENABLE_ADVANCED_PDF_OCR = os.getenv('ENABLE_ADVANCED_PDF_OCR', 'False') == 'True'

# Windows Tesseract Configuration
if os.name == 'nt':
    tesseract_path = r"D:\OCR\tesseract.exe"
    if os.path.exists(tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
    else:
        logger.warning(f"Tesseract executable not found at {tesseract_path}")
else:
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# Startup check
try:
    tesseract_version = pytesseract.get_tesseract_version()
    logger.info(f"Tesseract OCR engine initialized successfully. Version: {tesseract_version}")
except Exception as e:
    logger.error("Tesseract OCR engine not installed/configured. Please install Tesseract OCR.")

class DocumentExtractor:
    @staticmethod
    def preprocess_image(img):
        """Preprocesses images mildly to improve OCR accuracy."""
        logger.info("[OCR] Running preprocessing...")
        if img.mode != 'RGB':
            img = img.convert('RGB')
        # 1. Grayscale
        img = ImageOps.grayscale(img)
        # 2. Mild Contrast Enhancement
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        # Temporarily disabled sharpness and binarization as they may erase thin text
        return img

    @staticmethod
    def extract_text(file_path):
        text = ""
        method_used = "FAILED"
        
        logger.info(f"[OCR] Processing file: {file_path}")
        if not os.path.exists(file_path):
            logger.error("[OCR] File not found on disk.")
            return "[OCR_ERROR] File not found on disk.", method_used
            
        try:
            if file_path.lower().endswith('.pdf'):
                logger.info("[OCR] Detected extension: .pdf")
                # PASS 1: Native PDF Text Extraction
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                
                # PASS 2: If native text is too short, it's a scanned PDF.
                if len(text.strip()) < 50:
                    logger.info("[OCR] PDF text < 50 chars. Scanned PDF detected.")
                    text = ""
                    if ENABLE_ADVANCED_PDF_OCR:
                        method_used = "OCR_IMAGE"
                        try:
                            from pdf2image import convert_from_path
                            images = convert_from_path(file_path)
                            for img in images:
                                processed_img = DocumentExtractor.preprocess_image(img)
                                text += pytesseract.image_to_string(processed_img) + "\n"
                        except ImportError:
                            return "[OCR_ERROR] Advanced OCR enabled but pdf2image is not installed.", "FAILED"
                        except Exception as e:
                            logger.error(f"[OCR] pdf2image conversion failed: {str(e)}")
                            return f"[OCR_ERROR] pdf2image conversion failed (Poppler may be missing): {str(e)}", "FAILED"
                    else:
                        method_used = "FAILED"
                        return "[SCANNED_PDF] Scanned PDF OCR requires Poppler support. Local analysis disabled.", method_used
                else:
                    method_used = "PDF_TEXT"
                    
            elif file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp')):
                logger.info("[OCR] Detected extension: Image (png/jpg/etc)")
                method_used = "OCR_IMAGE"
                img = Image.open(file_path)
                logger.info(f"[OCR] Loaded image successfully. Size: {img.size[0]}x{img.size[1]}")
                processed_img = DocumentExtractor.preprocess_image(img)
                text = pytesseract.image_to_string(processed_img)
            else:
                logger.error("[OCR] Unsupported file format.")
                return "[OCR_ERROR] Unsupported file format for OCR.", "FAILED"
                
            if not text.strip():
                logger.error("[OCR] File was parsed but OCR returned empty string.")
                return "[OCR_ERROR] File was parsed but no extractable text was found.", "FAILED"
                
            logger.info(f"[OCR] OCR output chars: {len(text)}")
            preview = text[:500].replace('\n', ' ')
            logger.info(f'[OCR] Preview:\n"{preview}..."')
            
        except pytesseract.TesseractNotFoundError:
            logger.error("[OCR] TesseractNotFoundError: Tesseract OCR is not installed or not in PATH.")
            return "[OCR_ERROR] Tesseract OCR is not installed on the system or not in PATH. Cannot extract image text.", "FAILED"
        except Exception as e:
            logger.error(f"[OCR] Fatal Exception during extraction:\n{traceback.format_exc()}")
            return f"[OCR_ERROR] Failed to extract text: {str(e)}", "FAILED"
        
        return text.strip(), method_used

class MedicalNLP:
    # A heuristic NLP ruleset for local execution mimicking real NLP extraction
    DISEASES_DB = [
        # General
        'fever', 'viral infection', 'diabetes', 'hypertension', 'covid-19', 'migraine', 'pneumonia', 'anemia', 'asthma',
        # Orthopedic
        'shoulder dislocation', 'fracture', 'mri', 'x-ray', 'rotator cuff', 'ligament', 'instability', 'arthritis', 'orthopedic injury',
        # Blood Test Findings
        'hemoglobin', 'leukocyte', 'neutrophils', 'lymphocytes', 'eosinophils', 'platelets', 'cbc', 'rbc', 'wbc', 'hematology', 'cholesterol'
    ]
    
    MEDICATIONS_DB = [
        'paracetamol', 'ibuprofen', 'amoxicillin', 'lisinopril', 'metformin', 
        'aspirin', 'acetaminophen', 'azithromycin', 'omeprazole', 'albuterol', 'diclofenac'
    ]
    
    @classmethod
    def analyze(cls, text):
        if not text or "[OCR_ERROR]" in text:
            return {
                "summary": "AI could not confidently analyze this document. OCR failed or no text found.",
                "conditions": [],
                "medications": [],
                "confidence": 0.0,
                "is_error": True,
                "raw_text": text
            }
            
        lower_text = text.lower()
        
        found_conditions = set()
        for disease in cls.DISEASES_DB:
            if re.search(r'\b' + re.escape(disease) + r'\b', lower_text):
                found_conditions.add(disease)
                
        found_medications = set()
        for med in cls.MEDICATIONS_DB:
            if re.search(r'\b' + re.escape(med) + r'\b', lower_text):
                found_medications.add(med)
                
        # Generate dynamic summary exclusively from findings
        if found_conditions or found_medications:
            cond_str = ", ".join(found_conditions) if found_conditions else "general symptoms"
            med_str = ", ".join(found_medications) if found_medications else "supportive care"
            
            # Simple context awareness based on keywords
            if any(term in found_conditions for term in ['hemoglobin', 'wbc', 'rbc', 'cbc', 'platelets']):
                summary = f"Blood test report detected. Analysis reveals findings related to {cond_str}. Recommended interventions or current treatments involve {med_str}."
            elif any(term in found_conditions for term in ['mri', 'x-ray', 'fracture', 'dislocation']):
                summary = f"Orthopedic imaging report detected. Findings consistent with {cond_str}. Recommended interventions involve {med_str}."
            else:
                summary = f"Patient document reveals findings consistent with {cond_str}. Recommended interventions or current treatments involve {med_str}."
                
            confidence = 0.88
        else:
            summary = "Document was successfully parsed, but no specific recognized medical conditions or medications were confidently extracted. Please review the raw text manually."
            confidence = 0.45
            
        return {
            "summary": summary,
            "conditions": list(found_conditions),
            "medications": list(found_medications),
            "confidence": confidence,
            "is_error": False,
            "raw_text": text
        }
