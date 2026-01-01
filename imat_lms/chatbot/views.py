import os
from difflib import SequenceMatcher
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView
from groq import Groq
from .serializers import ChatRequestSerializer, FAQSerializer
from .models import FAQ

# LMS-specific system prompt for the chatbot
SYSTEM_PROMPT = """You are a helpful AI assistant for IMAT (Intelligent Modular Academic Training) Learning Management System. 
Your role is to help students with questions about:
- Course enrollment and browsing
- Downloading lessons for offline study
- Finding assignments and recordings
- Progress tracking and cross-device synchronization
- Contacting tutors and support teams
- General learning platform features

Provide clear, concise, and helpful answers. If a question is outside the scope of the LMS, politely redirect the user to the appropriate resource.
Keep responses under 200 words and student-friendly."""


class FAQListView(ListAPIView):
    """Get all active FAQs, optionally filtered by category"""
    queryset = FAQ.objects.filter(is_active=True)
    serializer_class = FAQSerializer
    
    def get_queryset(self):
        category = self.request.query_params.get('category')
        queryset = FAQ.objects.filter(is_active=True)
        if category:
            queryset = queryset.filter(category=category)
        return queryset


class ChatAPIView(APIView):
    """Enhanced chatbot that checks FAQ first, then uses Groq API with system prompt"""
    
    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            message = serializer.validated_data["message"]
            
            # Step 1: Check FAQ for similar questions
            faq_response = self._find_relevant_faq(message)
            if faq_response:
                return Response({
                    "reply": faq_response,
                    "source": "faq"
                }, status=200)
            
            # Step 2: If no FAQ match, use Groq API
            api_key = os.environ.get("GROQ_API_KEY")
            if not api_key:
                return Response(
                    {"error": "GROQ_API_KEY not set"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            try:
                client = Groq(api_key=api_key)
                
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": message}
                    ],
                    max_tokens=300,
                    temperature=0.7
                )
                
                reply = response.choices[0].message.content
                
                # Custom greeting for 'hi', 'hello', 'hey'
                if message.strip().lower() in ["hi", "hello", "hey"]:
                    return Response({
                        "reply": "Welcome to IMAT Global! How can I help you?"
                    }, status=200)
                # Return the full reply, cleaned and formatted for IMAT chat
                return Response({
                    "reply": self._format_reply(reply)
                }, status=200)
            
            except Exception as e:
                return Response({
                    "error": str(e)
                }, status=500)
        
        return Response(serializer.errors, status=400)
    
    def _format_reply(self, reply):
        """
        Removes backslashes before quotes, formats numbered steps, and cleans up reply for IMAT chat.
        """
        import re
        # Remove backslashes before quotes
        reply = reply.replace('\\"', '"').replace('\\', '').replace('\n', ' ')
        # Format numbered steps as separate lines
        reply = re.sub(r'(\d+\. )', r'\n\1', reply)
        # Collapse multiple spaces
        reply = re.sub(r'\s+', ' ', reply)
        # Remove leading/trailing whitespace
        return reply.strip()

    def _find_relevant_faq(self, user_message, threshold=0.6):
        """
        Find FAQ answers for user message using similarity matching.
        Returns answer if similarity score > threshold, else None.
        """
        faqs = FAQ.objects.filter(is_active=True)
        
        best_match = None
        best_score = threshold
        
        for faq in faqs:
            # Calculate similarity between user message and FAQ question
            score = SequenceMatcher(
                None, 
                user_message.lower(), 
                faq.question.lower()
            ).ratio()
            
            if score > best_score:
                best_score = score
                best_match = faq.answer
        
        return best_match



