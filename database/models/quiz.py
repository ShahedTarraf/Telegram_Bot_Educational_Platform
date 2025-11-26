"""
Quiz Model - Auto-graded quizzes
نموذج الاختبارات التلقائية
"""
from datetime import datetime
from typing import List, Optional
from beanie import Document
from pydantic import Field, BaseModel


class QuizOption(BaseModel):
    """Quiz option model"""
    text: str
    is_correct: bool = False


class QuizQuestion(BaseModel):
    """Quiz question model"""
    question: str
    options: List[QuizOption]
    points: int = 1
    explanation: Optional[str] = None  # Explanation shown after answering


class QuizAttempt(BaseModel):
    """Quiz attempt model"""
    user_id: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    answers: List[int] = Field(default_factory=list)  # Index of selected option for each question
    score: Optional[int] = None
    max_score: Optional[int] = None
    passed: bool = False
    time_taken_seconds: Optional[int] = None


class Quiz(Document):
    """Quiz model with auto-grading"""
    title: str
    description: str
    instructions: Optional[str] = None
    
    # Classification
    related_to: str  # course, material
    related_id: str
    
    # Questions
    questions: List[QuizQuestion] = Field(default_factory=list)
    
    # Settings
    time_limit_minutes: Optional[int] = None  # Time limit in minutes
    pass_percentage: int = 60  # Minimum percentage to pass
    max_attempts: int = 3  # Maximum number of attempts allowed
    shuffle_questions: bool = True  # Shuffle question order
    shuffle_options: bool = True  # Shuffle option order
    show_correct_answers: bool = True  # Show correct answers after completion
    
    # Availability
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    
    # Attempts
    attempts: List[QuizAttempt] = Field(default_factory=list)
    
    # Metadata
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    
    class Settings:
        name = "quizzes"
        indexes = [
            "related_to",
            "related_id",
            ("related_to", "related_id"),
        ]
    
    def get_user_attempts(self, user_id: str) -> List[QuizAttempt]:
        """Get all attempts by a user"""
        return [a for a in self.attempts if a.user_id == user_id]
    
    def get_attempts_count(self, user_id: str) -> int:
        """Get number of attempts by user"""
        return len(self.get_user_attempts(user_id))
    
    def can_attempt(self, user_id: str) -> bool:
        """Check if user can attempt quiz"""
        if not self.is_active:
            return False
        
        # Check availability dates
        now = datetime.utcnow()
        if self.available_from and now < self.available_from:
            return False
        if self.available_until and now > self.available_until:
            return False
        
        # Check max attempts
        attempts_count = self.get_attempts_count(user_id)
        if attempts_count >= self.max_attempts:
            return False
        
        return True
    
    def get_best_attempt(self, user_id: str) -> Optional[QuizAttempt]:
        """Get best attempt by user"""
        attempts = self.get_user_attempts(user_id)
        completed = [a for a in attempts if a.completed_at is not None]
        
        if not completed:
            return None
        
        return max(completed, key=lambda a: a.score or 0)
    
    def calculate_score(self, answers: List[int]) -> tuple[int, int]:
        """Calculate score from answers"""
        score = 0
        max_score = 0
        
        for i, question in enumerate(self.questions):
            max_score += question.points
            
            if i < len(answers):
                selected_option = answers[i]
                if 0 <= selected_option < len(question.options):
                    if question.options[selected_option].is_correct:
                        score += question.points
        
        return score, max_score
    
    async def start_attempt(self, user_id: str) -> Optional[QuizAttempt]:
        """Start new quiz attempt"""
        if not self.can_attempt(user_id):
            return None
        
        attempt = QuizAttempt(user_id=user_id)
        self.attempts.append(attempt)
        self.updated_at = datetime.utcnow()
        await self.save()
        
        return attempt
    
    async def submit_attempt(
        self,
        user_id: str,
        answers: List[int]
    ) -> Optional[QuizAttempt]:
        """Submit and grade quiz attempt"""
        # Find the latest incomplete attempt
        user_attempts = [a for a in self.attempts if a.user_id == user_id]
        incomplete = [a for a in user_attempts if a.completed_at is None]
        
        if not incomplete:
            return None
        
        attempt = incomplete[-1]
        
        # Calculate score
        score, max_score = self.calculate_score(answers)
        percentage = (score / max_score * 100) if max_score > 0 else 0
        
        # Update attempt
        attempt.completed_at = datetime.utcnow()
        attempt.answers = answers
        attempt.score = score
        attempt.max_score = max_score
        attempt.passed = percentage >= self.pass_percentage
        attempt.time_taken_seconds = int(
            (attempt.completed_at - attempt.started_at).total_seconds()
        )
        
        self.updated_at = datetime.utcnow()
        await self.save()
        
        return attempt
    
    def get_question_result(
        self,
        question_index: int,
        selected_option: int
    ) -> dict:
        """Get result for a specific question"""
        if question_index >= len(self.questions):
            return {}
        
        question = self.questions[question_index]
        
        if selected_option < 0 or selected_option >= len(question.options):
            return {
                'is_correct': False,
                'explanation': None,
                'correct_answer': None
            }
        
        selected = question.options[selected_option]
        correct_index = next(
            (i for i, opt in enumerate(question.options) if opt.is_correct),
            None
        )
        
        return {
            'is_correct': selected.is_correct,
            'explanation': question.explanation,
            'correct_answer_index': correct_index,
            'correct_answer_text': question.options[correct_index].text if correct_index is not None else None
        }
    
    def get_info_text(self) -> str:
        """Get formatted quiz info"""
        info = f"📝 **{self.title}**\n\n"
        info += f"{self.description}\n\n"
        
        if self.instructions:
            info += f"📋 **التعليمات:**\n{self.instructions}\n\n"
        
        info += f"❓ **عدد الأسئلة:** {len(self.questions)}\n"
        
        if self.time_limit_minutes:
            info += f"⏱️ **الوقت المحدد:** {self.time_limit_minutes} دقيقة\n"
        
        info += f"✅ **نسبة النجاح:** {self.pass_percentage}%\n"
        info += f"🔄 **المحاولات المسموحة:** {self.max_attempts}\n"
        
        if self.available_until:
            info += f"📅 **متاح حتى:** {self.available_until.strftime('%Y-%m-%d %H:%M')}\n"
        
        return info
