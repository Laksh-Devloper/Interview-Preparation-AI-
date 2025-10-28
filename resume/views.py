from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import ResumeForm
import os
import json
import google.generativeai as genai
from PyPDF2 import PdfReader
import docx

# Configure Gemini AI (add your API key)
genai.configure(api_key="Find your own pls ")

def extract_text_from_pdf(file_path):
    text = ""
    reader = PdfReader(file_path)
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

def home(request):
    return render(request, 'resume/index.html')

def upload_resume(request):
    """Updated to redirect to personality selection"""
    if request.method == 'POST':
        form = ResumeForm(request.POST, request.FILES)
        if form.is_valid():
            resume = form.save()
            file_path = resume.file.path
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext == ".pdf":
                resume_text = extract_text_from_pdf(file_path)
            elif ext == ".docx":
                resume_text = extract_text_from_docx(file_path)
            else:
                resume_text = "Unsupported file format."
            
            # Store resume text in session for interview
            request.session['resume_text'] = resume_text
            request.session['resume_id'] = resume.id
            
            # Redirect to personality selection instead of interview
            return redirect('select_personality')
    else:
        form = ResumeForm()
    return render(request, 'resume/upload.html', {'form': form})


def interview_session(request):
    """Main interview page with video and AI chat"""
    resume_text = request.session.get('resume_text', '')
    if not resume_text:
        return redirect('upload_resume')
    
    return render(request, 'resume/interview.html', {
        'resume_text': resume_text
    })

@csrf_exempt
def generate_questions(request):
    """Updated to include personality"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            resume_text = request.session.get('resume_text', '')
            personality = request.session.get('interviewer_personality', 'friendly')
            
            if not resume_text:
                return JsonResponse({'error': 'No resume found'}, status=400)
            
            # Generate personality-specific questions
            questions = generate_interview_questions(resume_text, personality)
            
            return JsonResponse({
                'questions': questions,
                'personality': personality,
                'success': True
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)


@csrf_exempt
def analyze_response(request):
    """API endpoint to analyze user responses"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            question = data.get('question', '')
            response = data.get('response', '')
            resume_text = request.session.get('resume_text', '')
            
            # Analyze response using Gemini
            analysis = analyze_interview_response(question, response, resume_text)
            
            return JsonResponse({
                'analysis': analysis,
                'success': True
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)

@csrf_exempt
def generate_report(request):
    """Generate final interview report"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            responses = data.get('responses', [])
            questions = data.get('questions', [])
            resume_text = request.session.get('resume_text', '')
            
            # Generate comprehensive report
            report = generate_interview_report(questions, responses, resume_text)
            
            return JsonResponse({
                'report': report,
                'success': True
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)

import json
from django.utils import timezone

def interview_results(request):
    """Display interview results page with real data"""
    # Get interview data from session
    interview_data = request.session.get('interview_results', {})
    
    # If no data in session, redirect back to upload
    if not interview_data:
        return redirect('upload_resume')
    
    # Convert to JSON string for safe template rendering
    interview_data_json = json.dumps(interview_data)
    
    return render(request, 'resume/results.html', {
        'interview_data_json': interview_data_json,
        'has_data': True
    })

@csrf_exempt  
def save_interview_results(request):
    """Save interview results to session with AI analysis"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Get resume text for AI analysis
            resume_text = request.session.get('resume_text', '')
            
            # Generate AI report using your existing function
            questions = data.get('questions', [])
            responses = data.get('responses', [])
            ai_report = ""
            
            if questions and responses and resume_text:
                try:
                    ai_report = generate_interview_report(questions, responses, resume_text)
                except Exception as e:
                    print(f"Error generating AI report: {e}")
                    ai_report = "AI analysis in progress..."
            
            # Store comprehensive results in session
            interview_results = {
                'score': float(data.get('score', 0)),
                'duration': data.get('duration', '0:00'),
                'questions_answered': data.get('questions_answered', 0),
                'total_questions': data.get('total_questions', 8),
                'responses': data.get('responses', []),
                'questions': data.get('questions', []),
                'ai_report': ai_report,  # Add AI generated report
                'session_data': {
                    'avg_response_time': data.get('session_data', {}).get('avg_response_time', '0s'),
                    'completion_rate': data.get('session_data', {}).get('completion_rate', 0)
                },
                'timestamp': timezone.now().isoformat()
            }
            
            request.session['interview_results'] = interview_results
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            print(f"Error saving results: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)

def upload_success(request):
    """Legacy success page - now redirects to interview"""
    return redirect('interview_session')


@csrf_exempt
def calculate_score(request):
    """Updated to include personality in scoring"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            questions = data.get('questions', [])
            responses = data.get('responses', [])
            duration = data.get('duration', '0:00')
            session_info = data.get('session_info', {})
            resume_text = request.session.get('resume_text', '')
            personality = request.session.get('interviewer_personality', 'friendly')
            
            # Get AI score with personality context
            score = generate_ai_score(questions, responses, duration, session_info, resume_text, personality)
            
            return JsonResponse({
                'success': True,
                'score': score
            })
            
        except Exception as e:
            print(f"Error calculating AI score: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)

def generate_ai_score(questions, responses, duration, session_info, resume_text, personality='friendly'):
    """Updated scoring with personality context"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Personality-specific evaluation criteria
        personality_context = {
            'strict': "As a STRICT HR interviewer, you expect structured, professional responses with clear examples and no rambling.",
            'friendly': "As a FRIENDLY HR interviewer, you value cultural fit, collaboration, and positive energy while maintaining professional standards.",
            'technical': "As a TECHNICAL LEAD, you focus on depth of technical knowledge, problem-solving ability, and concrete project experience.",
            'stress': "As a STRESS-TESTING interviewer, you evaluate how well candidates handle pressure, defend their positions, and maintain composure."
        }
        
        # Format Q&A pairs
        qa_pairs = ""
        for i, (q, r) in enumerate(zip(questions, responses), 1):
            qa_pairs += f"\nQ{i}: {q}\nA{i}: {r}\n"
        
        prompt = f"""
        {personality_context.get(personality, personality_context['friendly'])}
        
        Rate this interview performance on a scale of 1-10 (decimals allowed).

        INTERVIEW DATA:
        Interviewer Type: {personality.title()}
        Resume Context: {resume_text[:500]}...
        Duration: {duration}
        Questions Attempted: {len(responses)} out of {len(questions)}
        
        Q&A Session:
        {qa_pairs}
        
        PERSONALITY-SPECIFIC SCORING:
        For {personality} interviewer style, evaluate based on:
        - Response appropriateness for this interview style
        - How well candidate adapted to the interviewer personality
        - Meeting the expectations of this specific interviewer type
        
        Return ONLY a single number (e.g., 7.5, 8.2, 6.0) representing the overall interview score.
        """
        
        response = model.generate_content(prompt)
        score_text = response.text.strip()
        
        # Extract numeric score
        try:
            score = float(score_text)
            return max(1.0, min(10.0, score))
        except ValueError:
            import re
            numbers = re.findall(r'\d+\.?\d*', score_text)
            if numbers:
                score = float(numbers[0])
                return max(1.0, min(10.0, score))
            else:
                return 5.0
        
    except Exception as e:
        print(f"Error generating AI score: {e}")
        return 5.0    


def select_personality(request):
    """Personality selection page after resume upload"""
    resume_text = request.session.get('resume_text', '')
    if not resume_text:
        return redirect('upload_resume')
    
    if request.method == 'POST':
        personality = request.POST.get('personality')
        if personality in ['strict', 'friendly', 'technical', 'stress']:
            request.session['interviewer_personality'] = personality
            return redirect('interview_session')
        else:
            # Handle invalid personality selection
            return render(request, 'resume/personality.html', {
                'error': 'Please select a valid interviewer personality.'
            })
    
    return render(request, 'resume/personality.html')


# AI Helper Functions
def generate_interview_questions(resume_text, personality='friendly'):
    """Updated to generate personality-specific questions"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Personality-specific prompts
        personality_prompts = {
            'strict': """
            You are a STRICT, FORMAL HR interviewer. Generate exactly 8 professional interview questions.
            - Be formal and serious in tone
            - Focus on behavioral and situational questions
            - Ask questions that require structured, detailed responses
            - Include questions about handling pressure, leadership, and problem-solving
            - Questions should test if candidate can give organized, professional answers
            """,
            
            'friendly': """
            You are a FRIENDLY, WELCOMING HR interviewer. Generate exactly 8 warm but professional interview questions.
            - Start with easy, comfortable questions to break the ice
            - Focus on culture fit, teamwork, and personality
            - Ask about motivations, interests, and values
            - Keep questions approachable but still evaluate skills
            - Include questions about collaboration and work environment preferences
            """,
            
            'technical': """
            You are a TECHNICAL LEAD interviewer. Generate exactly 8 technical and project-focused questions.
            - Be direct and focused on technical competence
            - Ask about specific projects, technologies, and implementations
            - Include questions about problem-solving approaches
            - Ask why they chose certain technologies or methods
            - Focus on depth of technical understanding, not just surface knowledge
            """,
            
            'stress': """
            You are a CHALLENGING interviewer who tests candidates under pressure. Generate exactly 8 probing questions.
            - Ask questions that require quick thinking
            - Include hypothetical challenging scenarios
            - Ask questions that might make candidates defend their choices
            - Include questions about handling criticism and failure
            - Focus on resilience, adaptability, and confidence under pressure
            """
        }
        
        base_prompt = personality_prompts.get(personality, personality_prompts['friendly'])
        
        prompt = f"""
        {base_prompt}
        
        Based on the following resume, generate exactly 8 interview questions relevant to this candidate:
        
        Resume:
        {resume_text}
        
        Return ONLY the questions in this format:
        1. Question 1
        2. Question 2
        3. Question 3
        4. Question 4
        5. Question 5
        6. Question 6
        7. Question 7
        8. Question 8
        """
        
        response = model.generate_content(prompt)
        questions_text = response.text.strip()
        
        # Parse questions into a list
        questions = []
        for line in questions_text.split('\n'):
            line = line.strip()
            if line and any(line.startswith(f'{i}.') for i in range(1, 9)):
                question = line.split('.', 1)[1].strip()
                questions.append(question)
        
        return questions[:8]
        
    except Exception as e:
        print(f"Error generating questions: {e}")
        # Personality-specific fallback questions
        fallbacks = {
            'strict': [
                "Tell me about yourself and your professional background.",
                "Describe a time when you had to handle a difficult situation at work.",
                "How do you prioritize tasks when facing multiple deadlines?",
                "Give me an example of when you showed leadership.",
                "Describe a time you failed and how you handled it.",
                "How do you handle constructive criticism?",
                "Tell me about a time you had to work with a difficult team member.",
                "What are your long-term career goals?"
            ],
            'friendly': [
                "What interests you most about working with our company?",
                "Tell me about a project you're particularly proud of.",
                "How do you like to collaborate with team members?",
                "What motivates you in your daily work?",
                "Describe your ideal work environment.",
                "What do you do to stay current in your field?",
                "Tell me about a time when you helped a colleague.",
                "What are you looking for in your next role?"
            ],
            'technical': [
                "Walk me through a challenging technical project you've worked on.",
                "What technologies and frameworks are you most comfortable with?",
                "How do you approach debugging a complex issue?",
                "Explain a technical decision you made and why you chose that approach.",
                "How do you stay updated with new technologies?",
                "Describe your experience with version control and deployment processes.",
                "What's the most complex algorithm or system you've implemented?",
                "How do you ensure code quality and maintainability?"
            ],
            'stress': [
                "Tell me about a time when everything went wrong on a project.",
                "How do you handle working under extreme pressure?",
                "Describe a situation where you disagreed with your manager.",
                "What would you do if you realized you made a significant mistake?",
                "How do you respond when someone questions your expertise?",
                "Tell me about a time you had to deliver bad news to stakeholders.",
                "What's your biggest professional weakness?",
                "How do you handle multiple conflicting priorities?"
            ]
        }
        return fallbacks.get(personality, fallbacks['friendly'])

def analyze_interview_response(question, response, resume_text):
    """Analyze a single interview response"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Analyze this interview response and provide brief feedback:
        
        Question: {question}
        Response: {response}
        Resume Context: {resume_text[:500]}...
        
        Provide feedback in 2-3 sentences focusing on:
        - Relevance to the question
        - Use of specific examples
        - Areas for improvement
        
        Keep the feedback constructive and encouraging.
        """
        
        response_obj = model.generate_content(prompt)
        return response_obj.text.strip()
        
    except Exception as e:
        return "Thank you for your response. Let's continue with the next question."

def generate_interview_report(questions, responses, resume_text):
    """Generate comprehensive interview report"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        qa_pairs = ""
        for i, (q, r) in enumerate(zip(questions, responses), 1):
            qa_pairs += f"\nQ{i}: {q}\nA{i}: {r}\n"
        
        prompt = f"""
        Generate a comprehensive interview performance report based on:
        
        Resume: {resume_text[:800]}...
        
        Interview Q&A:
        {qa_pairs}
        
        Provide a report with:
        1. Overall Performance (Good/Needs Improvement/Excellent)
        2. Strengths (2-3 points)
        3. Areas for Improvement (2-3 points)
        4. Specific Recommendations (2-3 actionable tips)
        5. Overall Score (1-10) (Be blubt with score grant score above 5 only if all the questions are answered with precise communication and detailed expereicneces otherwise give overaallcsocre below 5 or 0 with bad performance tag )
        
        Keep it professional and constructive.
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        return "Interview completed successfully. Detailed analysis is being processed."
