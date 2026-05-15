"""
VQA Model using BLIP (Bootstrapping Language-Image Pre-training)
Pre-trained model from Hugging Face Transformers
"""

import torch
from transformers import BlipProcessor, BlipForQuestionAnswering
from PIL import Image
import os


class VQAModel:
    def __init__(self, device=None):
        """
        Initialize the VQA model
        
        Args:
            device: torch device (cuda or cpu)
        """
        # Set device
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = device
        
        print(f"Using device: {self.device}")
        
        # Load pre-trained model and processor
        self.model_name = "Salesforce/blip-vqa-base"
        print(f"Loading model: {self.model_name}")
        
        self.processor = BlipProcessor.from_pretrained(self.model_name)
        self.model = BlipForQuestionAnswering.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16 if self.device.type == "cuda" else torch.float32
        )
        self.model.to(self.device)
        self.model.eval()
        
        print("Model loaded successfully!")
    
    def predict_answer(self, image_path, question):
        """
        Generate an answer to a question about an image
        
        Args:
            image_path (str): Path to the image file
            question (str): Question about the image
            
        Returns:
            str: Answer to the question
        """
        try:
            # Load and prepare image
            if not os.path.exists(image_path):
                return "Error: Image file not found"
            
            image = Image.open(image_path).convert('RGB')
            
            # Process inputs
            inputs = self.processor(image, question, return_tensors="pt").to(self.device)
            
            # Generate answer
            with torch.no_grad():
                output = self.model.generate(**inputs, max_length=50)
            
            # Decode answer
            answer = self.processor.decode(output[0], skip_special_tokens=True)
            
            return answer
        
        except Exception as e:
            return f"Error processing image: {str(e)}"


# Global model instance
vqa_model = None


def load_model(device=None):
    """Load the VQA model globally"""
    global vqa_model
    if vqa_model is None:
        vqa_model = VQAModel(device=device)
    return vqa_model


def get_model():
    """Get the global VQA model instance"""
    global vqa_model
    if vqa_model is None:
        vqa_model = load_model()
    return vqa_model
