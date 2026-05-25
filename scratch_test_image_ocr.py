import os
import logging
from PIL import Image, ImageDraw, ImageFont
import pytesseract
from intelligence.services.extractor import DocumentExtractor, MedicalNLP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("--- OCR IMAGE DEBUG TEST ---")

# 1. Create a Mock Blood Report Image
img_path = "debug_blood_report.png"
img = Image.new('RGB', (800, 1000), color = (255, 255, 255))
d = ImageDraw.Draw(img)
# Using a generic font 
d.text((50, 50), "COMPLETE BLOOD COUNT (CBC)", fill=(0,0,0))
d.text((50, 100), "HEMOGLOBIN             15.2 g/dl", fill=(0,0,0))
d.text((50, 150), "TOTAL LEUKOCYTE COUNT  8500 /cumm", fill=(0,0,0))
d.text((50, 200), "NEUTROPHILS            65 %", fill=(0,0,0))
d.text((50, 250), "LYMPHOCYTES            28 %", fill=(0,0,0))
d.text((50, 300), "PLATELET COUNT         250000 /cumm", fill=(0,0,0))
d.text((50, 350), "RBC COUNT              5.1 mill/cumm", fill=(0,0,0))
d.text((50, 450), "Remarks: Mild eosinophilia.", fill=(0,0,0))
img.save(img_path)

print(f"\nCreated mock image: {img_path}")

# 2. Run Extractor
print("\n[RUNNING EXTRACTOR]")
text, method = DocumentExtractor.extract_text(img_path)

print("\n[OCR RESULT]")
print(f"Method: {method}")
print(f"Text Length: {len(text)}")
print(f"Text Preview:\n{text}")

# 3. Run Medical NLP
print("\n[RUNNING NLP ANALYZER]")
analysis = MedicalNLP.analyze(text)

print("\n[NLP RESULT]")
print(f"Summary: {analysis['summary']}")
print(f"Conditions: {analysis['conditions']}")
print(f"Medications: {analysis['medications']}")
print(f"Confidence: {analysis['confidence']}")

# Verify extraction worked
assert "hemoglobin" in analysis['conditions'], "Failed to extract hemoglobin"
assert "leukocyte" in analysis['conditions'], "Failed to extract leukocyte count"

# Cleanup
if os.path.exists(img_path):
    os.remove(img_path)

print("\n--- OCR TEST COMPLETED SUCCESSFULLY ---")
