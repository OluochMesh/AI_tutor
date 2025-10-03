# calls the AI api
import os
import requests
import json
import re

class AITutorService:
    def __init__(self):
        self.api_key = os.environ.get('HUGGINGFACE_API_KEY', '')
        # Using free Hugging Face Inference API
        self.api_url = "https://api-inference.huggingface.co/models/google/flan-t5-large"
        
    def analyze_explanation(self, concept, learner_input):
        """
        Analyze learner's explanation using Hugging Face API
        
        Args:
            concept (str): The topic being studied
            learner_input (str): What the learner explained
            
        Returns:
            dict: {
                'feedback': str,
                'understanding_score': float (0-1),
                'strengths': list,
                'areas_to_improve': list
            }
        """
        try:
            # Create a prompt for the model
            prompt = f"""Analyze this student explanation about {concept}: "{learner_input}"
            
Provide: 1) Feedback (2 sentences), 2) Score 0-1, 3) What they got right, 4) What to improve.
Keep response concise."""

            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 250,
                    "temperature": 0.7
                }
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_text = result[0]['generated_text'] if isinstance(result, list) else result.get('generated_text', '')
                
                # Parse the AI response and extract feedback
                feedback = self._extract_feedback(ai_text, concept, learner_input)
                score = self._calculate_score(learner_input, concept)
                
                return {
                    'feedback': feedback,
                    'understanding_score': score,
                    'strengths': self._extract_strengths(learner_input),
                    'areas_to_improve': self._extract_improvements(concept)
                }
            else:
                # Fallback response if API fails
                return self._create_fallback_response(concept, learner_input)
                
        except Exception as e:
            print(f"AI Service Error: {str(e)}")
            return self._create_fallback_response(concept, learner_input)
    
    def _extract_feedback(self, ai_text, concept, learner_input):
        """Extract or generate feedback from AI response"""
        if ai_text and len(ai_text) > 20:
            # Clean up AI response
            feedback = ai_text.strip()
            if len(feedback) > 200:
                feedback = feedback[:200] + "..."
            return feedback
        
        # Generate basic feedback
        word_count = len(learner_input.split())
        if word_count < 15:
            return f"Good start on {concept}! Try to expand your explanation with more details and examples."
        else:
            return f"Nice explanation of {concept}! You've covered the main points. Consider adding specific examples to strengthen your understanding."
    
    def _calculate_score(self, explanation, concept):
        """Calculate understanding score based on explanation quality"""
        score = 0.5  # Base score
        
        word_count = len(explanation.split())
        
        # Length factor (longer explanations usually show better understanding)
        if word_count >= 50:
            score += 0.2
        elif word_count >= 30:
            score += 0.15
        elif word_count >= 20:
            score += 0.1
        
        # Keyword relevance (simple check)
        concept_words = concept.lower().split()
        explanation_lower = explanation.lower()
        
        keyword_matches = sum(1 for word in concept_words if word in explanation_lower)
        if keyword_matches > 0:
            score += min(0.2, keyword_matches * 0.1)
        
        # Check for explanatory words (shows deeper understanding)
        explanatory_words = ['because', 'therefore', 'thus', 'since', 'as a result', 'which means', 'leads to']
        if any(word in explanation_lower for word in explanatory_words):
            score += 0.1
        
        return round(min(1.0, score), 2)
    
    def _extract_strengths(self, explanation):
        """Extract strengths from the explanation"""
        strengths = []
        
        if len(explanation.split()) >= 20:
            strengths.append("Provided detailed explanation")
        
        if any(word in explanation.lower() for word in ['example', 'instance', 'such as']):
            strengths.append("Used examples to illustrate points")
        
        if any(word in explanation.lower() for word in ['because', 'therefore', 'thus']):
            strengths.append("Explained cause and effect relationships")
        
        if not strengths:
            strengths.append("Attempted to explain the concept")
        
        return strengths
    
    def _extract_improvements(self, concept):
        """Suggest areas for improvement"""
        return [
            f"Add more specific details about {concept}",
            "Include real-world examples",
            "Explain the underlying mechanisms"
        ]
    
    def _create_fallback_response(self, concept, learner_input):
        """Create a basic response when AI is unavailable"""
        score = self._calculate_score(learner_input, concept)
        
        return {
            'feedback': f"Thank you for your explanation about {concept}. You've made a good attempt. Keep practicing and try to add more specific details!",
            'understanding_score': score,
            'strengths': self._extract_strengths(learner_input),
            'areas_to_improve': self._extract_improvements(concept)
        }
    
    def generate_study_tips(self, weak_topics):
        """
        Generate study tips for weak topics
        
        Args:
            weak_topics (list): List of topics where user needs improvement
            
        Returns:
            str: Study recommendations
        """
        if not weak_topics:
            return "Keep up the great work! Continue practicing regularly."
        
        try:
            topics_str = ", ".join(weak_topics)
            prompt = f"Give 3 study tips for learning: {topics_str}. Be brief and practical."
            
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 150,
                    "temperature": 0.8
                }
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=20
            )
            
            if response.status_code == 200:
                result = response.json()
                tips = result[0]['generated_text'] if isinstance(result, list) else result.get('generated_text', '')
                return tips.strip() if tips else self._fallback_study_tips(weak_topics)
            else:
                return self._fallback_study_tips(weak_topics)
                
        except Exception as e:
            print(f"Study tips error: {str(e)}")
            return self._fallback_study_tips(weak_topics)
    
    def _fallback_study_tips(self, weak_topics):
        """Fallback study tips when API unavailable"""
        tips = [
            f"Review the fundamentals of {', '.join(weak_topics)}",
            "Practice with real-world examples and case studies",
            "Create summary notes and flashcards for quick review",
            "Test yourself regularly to reinforce learning"
        ]
        return "\n".join(f"{i+1}. {tip}" for i, tip in enumerate(tips))