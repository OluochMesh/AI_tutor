import os
import requests
import json
import re

class AITutorService:
    def __init__(self):
        self.api_key = os.environ.get('HUGGINGFACE_API_KEY', '')
        # Free-tier Hugging Face Inference API
        self.api_url = "https://api-inference.huggingface.co/models/google/flan-t5-xl"

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
            # 🧠 Smarter, structured prompt
            prompt = f"""
You are an educational AI tutor. Respond ONLY with valid JSON in this exact structure:

{{
  "feedback": "Your feedback here",
  "understanding_score": 0.0,
  "strengths": ["point 1", "point 2"],
  "areas_to_improve": ["point 1", "point 2"]
}}

Now, analyze the student's explanation about "{concept}" below:
"{learner_input}"

Evaluate it as follows:
1. Provide constructive feedback (2-3 short, supportive sentences)
2. Assign a score between 0 and 1 (0=poor, 1=excellent)
3. List strengths and areas to improve
"""

            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 300,
                    "temperature": 0.7
                }
            }

            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=40
            )

            if response.status_code == 200:
                result = response.json()
                ai_text = result[0]['generated_text'] if isinstance(result, list) else result.get('generated_text', '')
                
                # Try to parse AI output into JSON
                parsed = self._parse_ai_response(ai_text)
                if parsed:
                    return parsed

                # Fallback: structured partial response
                feedback = self._extract_feedback(ai_text, concept, learner_input)
                score = self._calculate_score(learner_input, concept)
                return {
                    'feedback': feedback,
                    'understanding_score': score,
                    'strengths': self._extract_strengths(learner_input),
                    'areas_to_improve': self._extract_improvements(concept)
                }

            else:
                return self._create_fallback_response(concept, learner_input)

        except Exception as e:
            print(f"AI Service Error: {str(e)}")
            return self._create_fallback_response(concept, learner_input)

    def _parse_ai_response(self, text):
        """Try to extract and parse JSON safely from AI output"""
        if not text:
            return None

        # Extract JSON substring if model adds extra text
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if not match:
            return None

        try:
            cleaned = match.group(0)
            data = json.loads(cleaned)
            # Ensure all expected keys exist
            if all(k in data for k in ["feedback", "understanding_score", "strengths", "areas_to_improve"]):
                return data
        except Exception:
            return None

        return None

    def _extract_feedback(self, ai_text, concept, learner_input):
        """Fallback feedback generator"""
        if ai_text and len(ai_text.strip()) > 20:
            feedback = ai_text.strip()
            if len(feedback) > 300:
                feedback = feedback[:300] + "..."
            return feedback
        
        # Simple fallback based on input length
        word_count = len(learner_input.split())
        if word_count < 15:
            return f"Good start on {concept}! Try to expand your explanation with more details and examples."
        else:
            return f"Nice explanation of {concept}! You've covered key ideas. Add examples or definitions to deepen your understanding."

    def _calculate_score(self, explanation, concept):
        """Rudimentary heuristic score (used if AI JSON unavailable)"""
        score = 0.5
        word_count = len(explanation.split())

        if word_count >= 50:
            score += 0.2
        elif word_count >= 30:
            score += 0.15
        elif word_count >= 20:
            score += 0.1

        concept_words = concept.lower().split()
        explanation_lower = explanation.lower()
        keyword_matches = sum(1 for word in concept_words if word in explanation_lower)
        if keyword_matches > 0:
            score += min(0.2, keyword_matches * 0.1)

        if any(word in explanation_lower for word in ['because', 'therefore', 'thus', 'since', 'as a result']):
            score += 0.1

        return round(min(1.0, score), 2)

    def _extract_strengths(self, explanation):
        strengths = []
        if len(explanation.split()) >= 20:
            strengths.append("Provided detailed explanation")
        if any(word in explanation.lower() for word in ['example', 'instance', 'such as']):
            strengths.append("Used examples effectively")
        if any(word in explanation.lower() for word in ['because', 'therefore', 'thus']):
            strengths.append("Showed cause-effect reasoning")
        if not strengths:
            strengths.append("Attempted to explain concept")
        return strengths

    def _extract_improvements(self, concept):
        return [
            f"Add more specific details about {concept}",
            "Include real-world examples",
            "Explain the process or relationships more clearly"
        ]

    def _create_fallback_response(self, concept, learner_input):
        score = self._calculate_score(learner_input, concept)
        return {
            'feedback': f"Thanks for your explanation about {concept}. You’ve made a great start! Try adding key terms and examples to reinforce your understanding.",
            'understanding_score': score,
            'strengths': self._extract_strengths(learner_input),
            'areas_to_improve': self._extract_improvements(concept)
        }

    def generate_study_tips(self, weak_topics):
        """Generate personalized study tips for weak topics"""
        if not weak_topics:
            return "Keep up the great work! Continue practicing regularly."

        try:
            topics_str = ", ".join(weak_topics)
            prompt = f"""
You are an AI study coach. Give 3 short, practical study tips for improving in: {topics_str}.
Keep each tip under 20 words.
"""

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
        tips = [
            f"Review the basics of {', '.join(weak_topics)}",
            "Practice using flashcards or spaced repetition",
            "Summarize what you learn in your own words",
            "Teach the topic to a friend to test understanding"
        ]
        return "\n".join(f"{i+1}. {tip}" for i, tip in enumerate(tips))
