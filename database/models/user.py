"""
User Model
"""
from datetime import datetime
from typing import List, Optional
from beanie import Document
from pydantic import BaseModel, Field, EmailStr


class CourseEnrollment(BaseModel):
    """Course enrollment sub-document"""
    course_id: str
    enrolled_at: datetime = Field(default_factory=datetime.utcnow)
    payment_status: str = "pending"  # pending, paid, rejected
    payment_amount: int
    payment_method: Optional[str] = None  # Shap Cash, HERM
    payment_proof_file_id: Optional[str] = None
    approval_status: str = "pending"  # pending, approved, rejected
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    progress: int = 0  # 0-100
    videos_watched: List[str] = Field(default_factory=list)
    assignments_submitted: List[str] = Field(default_factory=list)
    exams_taken: List[str] = Field(default_factory=list)
    completed: bool = False
    certificate_issued: bool = False


class MaterialEnrollment(BaseModel):
    """Material enrollment sub-document"""
    material_id: str
    year: int
    semester: int
    enrolled_at: datetime = Field(default_factory=datetime.utcnow)
    payment_status: str = "pending"
    payment_amount: int
    payment_method: Optional[str] = None
    payment_proof_file_id: Optional[str] = None
    approval_status: str = "pending"
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    progress: int = 0
    videos_watched: List[str] = Field(default_factory=list)
    assignments_submitted: List[str] = Field(default_factory=list)
    exams_taken: List[str] = Field(default_factory=list)


class ProjectEnrollment(BaseModel):
    """Project enrollment sub-document"""
    project_id: str
    project_type: str  # semester, graduation
    title: str
    description: str
    proposal_status: str = "pending"  # pending, approved, rejected
    implementation_status: str = "not_started"  # not_started, in_progress, completed
    video_file_id: Optional[str] = None
    submitted_at: Optional[datetime] = None
    grade: Optional[int] = None
    feedback: Optional[str] = None


class User(Document):
    """User model"""
    telegram_id: int = Field(unique=True)
    full_name: str
    phone: str
    email: EmailStr = Field(unique=True)
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)
    blocked: bool = False
    
    # Enrollments
    courses: List[CourseEnrollment] = Field(default_factory=list)
    materials: List[MaterialEnrollment] = Field(default_factory=list)
    projects: List[ProjectEnrollment] = Field(default_factory=list)
    
    # Statistics
    total_videos_watched: int = 0
    total_assignments_submitted: int = 0
    total_exams_taken: int = 0
    total_points: int = 0
    
    class Settings:
        name = "users"
        indexes = [
            "telegram_id",
            "email",
        ]
    
    def get_course_enrollment(self, course_id: str) -> Optional[CourseEnrollment]:
        """Get course enrollment"""
        for enrollment in self.courses:
            if enrollment.course_id == course_id:
                return enrollment
        return None
    
    def get_material_enrollment(self, material_id: str) -> Optional[MaterialEnrollment]:
        """Get material enrollment"""
        for enrollment in self.materials:
            if enrollment.material_id == material_id:
                return enrollment
        return None
    
    def has_approved_course(self, course_id: str) -> bool:
        """Check if user has approved access to course"""
        enrollment = self.get_course_enrollment(course_id)
        return enrollment and enrollment.approval_status == "approved"
    
    def has_approved_material(self, material_id: str) -> bool:
        """Check if user has approved access to material"""
        enrollment = self.get_material_enrollment(material_id)
        return enrollment and enrollment.approval_status == "approved"
    
    async def add_course_enrollment(
        self,
        course_id: str,
        payment_amount: int,
        payment_method: str,
        payment_proof_file_id: str
    ):
        """Add course enrollment"""
        enrollment = CourseEnrollment(
            course_id=course_id,
            payment_amount=payment_amount,
            payment_method=payment_method,
            payment_proof_file_id=payment_proof_file_id,
            payment_status="paid"
        )
        self.courses.append(enrollment)
        await self.save()
    
    async def add_material_enrollment(
        self,
        material_id: str,
        year: int,
        semester: int,
        payment_amount: int,
        payment_method: str,
        payment_proof_file_id: str
    ):
        """Add material enrollment"""
        enrollment = MaterialEnrollment(
            material_id=material_id,
            year=year,
            semester=semester,
            payment_amount=payment_amount,
            payment_method=payment_method,
            payment_proof_file_id=payment_proof_file_id,
            payment_status="paid"
        )
        self.materials.append(enrollment)
        await self.save()
    
    async def update_last_active(self):
        """Update last active timestamp"""
        self.last_active = datetime.utcnow()
        await self.save()
