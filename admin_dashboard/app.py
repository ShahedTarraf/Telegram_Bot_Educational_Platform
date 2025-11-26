"""
Admin Dashboard - FastAPI Application
"""
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from loguru import logger
from pathlib import Path
import json

from config.settings import settings
from database.connection import init_db
from database.models.user import User
from database.models.notification import Notification


app = FastAPI(title="Educational Platform - Admin Dashboard")
templates = Jinja2Templates(directory="admin_dashboard/templates")
security = HTTPBasic()


# Static files (if exists)
try:
    app.mount("/static", StaticFiles(directory="admin_dashboard/static"), name="static")
except:
    pass


def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify admin credentials"""
    correct_username = secrets.compare_digest(credentials.username, settings.ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, settings.ADMIN_PASSWORD)
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("Starting Admin Dashboard...")
    await init_db()
    logger.info("Admin Dashboard ready!")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, username: str = Depends(verify_admin)):
    """Main dashboard"""
    # Get statistics
    total_users = await User.find().count()
    pending_approvals = await User.find(
        User.courses.approval_status == "pending"
    ).count()
    
    # Get recent users
    recent_users = await User.find().sort(-User.registered_at).limit(10).to_list()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "total_users": total_users,
        "pending_approvals": pending_approvals,
        "recent_users": recent_users,
        "username": username
    })


@app.get("/students", response_class=HTMLResponse)
async def students_list(request: Request, username: str = Depends(verify_admin)):
    """Students list"""
    students = await User.find().sort(-User.registered_at).to_list()
    
    return templates.TemplateResponse("students.html", {
        "request": request,
        "students": students,
        "username": username
    })


@app.get("/student/{telegram_id}", response_class=HTMLResponse)
async def student_detail(request: Request, telegram_id: int, username: str = Depends(verify_admin)):
    """Student detail"""
    student = await User.find_one(User.telegram_id == telegram_id)
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Enrich enrolled courses with course names
    enrolled_courses = []
    try:
        from config.courses_config import get_course
    except Exception:
        get_course = None  # Fallback if config not available
    
    for enrollment in student.courses:
        course_name = enrollment.course_id
        try:
            if get_course:
                course = get_course(enrollment.course_id)
                if course and course.get('name'):
                    course_name = course['name']
        except Exception as e:
            logger.error(f"Failed to load course name for {enrollment.course_id}: {e}")
        
        enrolled_courses.append({
            "course_id": enrollment.course_id,
            "course_name": course_name,
            "approval_status": enrollment.approval_status,
            "progress": enrollment.progress,
            "enrolled_at": enrollment.enrolled_at,
        })
    
    # Enrich enrolled materials
    enrolled_materials = []
    try:
        from config.materials_config import get_material
    except Exception:
        get_material = None
    
    for m in student.materials:
        material_name = m.material_id
        year = getattr(m, "year", None)
        semester = getattr(m, "semester", None)
        try:
            if get_material:
                material = get_material(m.material_id)
                if material and material.get('name'):
                    material_name = material['name']
                if material:
                    year = material.get('year', year)
                    semester = material.get('semester', semester)
        except Exception as e:
            logger.error(f"Failed to load material name for {m.material_id}: {e}")
        
        enrolled_materials.append({
            "material_id": m.material_id,
            "material_name": material_name,
            "year": year,
            "semester": semester,
            "approval_status": m.approval_status,
            "progress": m.progress,
            "enrolled_at": m.enrolled_at,
        })
    
    return templates.TemplateResponse("student_detail.html", {
        "request": request,
        "student": student,
        "enrolled_courses": enrolled_courses,
        "enrolled_materials": enrolled_materials,
        "username": username
    })


@app.post("/api/approve-course/{telegram_id}/{course_id}")
async def approve_course(telegram_id: int, course_id: str, username: str = Depends(verify_admin)):
    """Approve course enrollment"""
    from datetime import datetime
    
    user = await User.find_one(User.telegram_id == telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Find and approve course enrollment
    for enrollment in user.courses:
        if enrollment.course_id == course_id and enrollment.approval_status == "pending":
            enrollment.approval_status = "approved"
            enrollment.approved_by = username
            enrollment.approved_at = datetime.utcnow()
            await user.save()
            
            # Send notification to user
            notification = Notification(
                user_id=telegram_id,
                title="تم الموافقة على تسجيلك!",
                message=f"تم الموافقة على تسجيلك في الدورة.",
                notification_type="approval",
                related_id=course_id
            )
            await notification.insert()
            
            # Send telegram message directly
            from config.settings import settings
            import httpx
            try:
                from config.courses_config import get_course
                course = get_course(course_id)
                course_name = course['name'] if course else course_id
                link = None
                try:
                    if course and course.get('group_link'):
                        link = course['group_link']
                    else:
                        gl_path = Path('data/group_links.json')
                        if gl_path.exists():
                            with open(gl_path, 'r', encoding='utf-8') as f:
                                gl = json.load(f)
                                link = gl.get('courses', {}).get(course_id) or gl.get(course_id)
                except Exception as e:
                    logger.error(f"Error loading group link: {e}")
                
                text = f"""
🎉 **تم الموافقة على تسجيلك!**

✅ تم قبول طلب تسجيلك في:
📚 {course_name}

🔗 رابط الانضمام إلى مجموعة الدورة:
{link if link else 'سيتم إرسال رابط المجموعة قريباً'}

شكراً لثقتك! 🙏
                """
                
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
                        json={
                            "chat_id": telegram_id,
                            "text": text,
                            "parse_mode": "Markdown"
                        }
                    )
                logger.info(f"Notification sent to {telegram_id}")
            except Exception as e:
                logger.error(f"Failed to send telegram notification: {e}")
            
            logger.info(f"Course approved: {user.full_name} -> {course_id}")
            return {"status": "success", "message": "تم الموافقة بنجاح"}
    
    raise HTTPException(status_code=404, detail="Enrollment not found")


@app.post("/api/reject-course/{telegram_id}/{course_id}")
async def reject_course(telegram_id: int, course_id: str, username: str = Depends(verify_admin)):
    """Reject course enrollment"""
    user = await User.find_one(User.telegram_id == telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    for enrollment in user.courses:
        if enrollment.course_id == course_id and enrollment.approval_status == "pending":
            enrollment.approval_status = "rejected"
            enrollment.approved_by = username
            await user.save()
            
            # Send notification
            notification = Notification(
                user_id=telegram_id,
                title="تم رفض طلبك",
                message=f"تم رفض طلب التسجيل. يرجى التواصل مع الإدارة.",
                notification_type="approval",
                related_id=course_id
            )
            await notification.insert()
            
            logger.info(f"Course rejected: {user.full_name} -> {course_id}")
            return {"status": "success", "message": "تم الرفض"}
    
    raise HTTPException(status_code=404, detail="Enrollment not found")


@app.post("/api/approve-material/{telegram_id}/{material_id}")
async def approve_material(telegram_id: int, material_id: str, username: str = Depends(verify_admin)):
    """Approve material enrollment"""
    from datetime import datetime
    
    user = await User.find_one(User.telegram_id == telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Find and approve material enrollment
    for enrollment in user.materials:
        if enrollment.material_id == material_id and enrollment.approval_status == "pending":
            enrollment.approval_status = "approved"
            enrollment.approved_by = username
            enrollment.approved_at = datetime.utcnow()
            await user.save()
            
            # Send notification to user
            notification = Notification(
                user_id=telegram_id,
                title="تم الموافقة على تسجيلك!",
                message=f"تم الموافقة على تسجيلك في المادة.",
                notification_type="approval",
                related_id=material_id
            )
            await notification.insert()
            
            # Send telegram message directly
            from config.settings import settings
            import httpx
            try:
                from config.materials_config import get_material
                material = get_material(material_id)
                material_name = material['name'] if material else material_id
                link = None
                try:
                    if material and material.get('group_link'):
                        link = material['group_link']
                    else:
                        gl_path = Path('data/group_links.json')
                        if gl_path.exists():
                            with open(gl_path, 'r', encoding='utf-8') as f:
                                gl = json.load(f)
                                link = gl.get('materials', {}).get(material_id) or gl.get(material_id)
                except Exception as e:
                    logger.error(f"Error loading material group link: {e}")
                
                text = f"""
🎉 **تم الموافقة على تسجيلك!**

✅ تم قبول طلب تسجيلك في:
📚 {material_name} - السنة {enrollment.year} - الفصل {enrollment.semester}

🔗 رابط الانضمام إلى مجموعة المادة:
{link if link else 'سيتم إرسال رابط المجموعة قريباً'}

شكراً لثقتك! 🙏
                """
                
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
                        json={
                            "chat_id": telegram_id,
                            "text": text,
                            "parse_mode": "Markdown"
                        }
                    )
                logger.info(f"Notification sent to {telegram_id}")
            except Exception as e:
                logger.error(f"Failed to send telegram notification: {e}")
            
            logger.info(f"Material approved: {user.full_name} -> {material_id}")
            return {"status": "success", "message": "تم الموافقة بنجاح"}
    
    raise HTTPException(status_code=404, detail="Enrollment not found")


@app.post("/api/reject-material/{telegram_id}/{material_id}")
async def reject_material(telegram_id: int, material_id: str, username: str = Depends(verify_admin)):
    """Reject material enrollment"""
    user = await User.find_one(User.telegram_id == telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    for enrollment in user.materials:
        if enrollment.material_id == material_id and enrollment.approval_status == "pending":
            enrollment.approval_status = "rejected"
            enrollment.approved_by = username
            await user.save()
            
            # Send notification
            notification = Notification(
                user_id=telegram_id,
                title="تم رفض طلبك",
                message=f"تم رفض طلب التسجيل في المادة. يرجى التواصل مع الإدارة.",
                notification_type="approval",
                related_id=material_id
            )
            await notification.insert()
            
            logger.info(f"Material rejected: {user.full_name} -> {material_id}")
            return {"status": "success", "message": "تم الرفض"}
    
    raise HTTPException(status_code=404, detail="Enrollment not found")


@app.get("/pending-approvals", response_class=HTMLResponse)
async def pending_approvals(request: Request, username: str = Depends(verify_admin)):
    """Show pending approvals"""
    from config.settings import settings
    users = await User.find().to_list()
    
    pending_enrollments = []
    for user in users:
        # Check course enrollments
        for enrollment in user.courses:
            if enrollment.approval_status == "pending":
                from config.courses_config import get_course
                course = get_course(enrollment.course_id)
                
                # Create enrollment object with all needed data
                enrollment_data = {
                    "user": user,
                    "course_id": enrollment.course_id,
                    "course_name": course["name"] if course else enrollment.course_id,
                    "enrolled_at": enrollment.enrolled_at,
                    "payment_method": enrollment.payment_method,
                    "payment_proof_file_id": enrollment.payment_proof_file_id,
                    "status": enrollment.approval_status,
                    "bot_token": settings.TELEGRAM_BOT_TOKEN,
                    "type": "course"
                }
                pending_enrollments.append(enrollment_data)
        
        # Check material enrollments (جديد)
        for enrollment in user.materials:
            if enrollment.approval_status == "pending":
                from config.materials_config import get_material
                material = get_material(enrollment.material_id)
                
                # Create enrollment object with all needed data
                enrollment_data = {
                    "user": user,
                    "course_id": enrollment.material_id,
                    "course_name": f"{material['name']} - السنة {enrollment.year} - الفصل {enrollment.semester}" if material else enrollment.material_id,
                    "enrolled_at": enrollment.enrolled_at,
                    "payment_method": enrollment.payment_method,
                    "payment_proof_file_id": enrollment.payment_proof_file_id,
                    "status": enrollment.approval_status,
                    "bot_token": settings.TELEGRAM_BOT_TOKEN,
                    "type": "material"
                }
                pending_enrollments.append(enrollment_data)
    
    return templates.TemplateResponse("pending_approvals.html", {
        "request": request,
        "pending_enrollments": pending_enrollments,
        "username": username
    })


@app.get("/courses", response_class=HTMLResponse)
async def courses_list(request: Request, username: str = Depends(verify_admin)):
    """Courses management"""
    from config.courses_config import get_all_courses
    courses = get_all_courses()
    
    return templates.TemplateResponse("courses.html", {
        "request": request,
        "courses": courses,
        "username": username
    })


@app.get("/materials", response_class=HTMLResponse)
async def materials_list(request: Request, username: str = Depends(verify_admin)):
    """Materials management"""
    from config.materials_config import get_all_materials
    materials = get_all_materials()
    
    # Add default values for missing fields
    for material in materials:
        if 'price' not in material:
            material['price'] = 100000  # Default price
        if 'enrolled_count' not in material:
            material['enrolled_count'] = 0
    
    return templates.TemplateResponse("materials.html", {
        "request": request,
        "materials": materials,
        "username": username
    })


@app.get("/assignments", response_class=HTMLResponse)
async def assignments_list(request: Request, username: str = Depends(verify_admin)):
    """Assignments management"""
    from database.models.assignment import Assignment
    
    assignments = await Assignment.find().sort(-Assignment.created_at).to_list()
    
    # Calculate statistics for each assignment
    for assignment in assignments:
        assignment.total_submissions = len(assignment.submissions)
        assignment.graded_submissions = len([s for s in assignment.submissions if s.status == "graded"])
        assignment.pending_submissions = assignment.total_submissions - assignment.graded_submissions
    
    return templates.TemplateResponse("assignments.html", {
        "request": request,
        "assignments": assignments,
        "username": username
    })


@app.get("/certificates", response_class=HTMLResponse)
async def certificates_list(request: Request, username: str = Depends(verify_admin)):
    """Certificates management"""
    # TODO: Implement certificates from database
    certificates = []
    
    return templates.TemplateResponse("certificates.html", {
        "request": request,
        "certificates": certificates,
        "username": username
    })


@app.get("/notifications", response_class=HTMLResponse)
async def notifications_list(request: Request, username: str = Depends(verify_admin)):
    """Notifications management"""
    notifications = await Notification.find().sort(-Notification.created_at).limit(100).to_list()
    
    return templates.TemplateResponse("notifications.html", {
        "request": request,
        "notifications": notifications,
        "username": username
    })


@app.post("/api/send-notification")
async def send_notification(
    request: Request,
    username: str = Depends(verify_admin)
):
    """Send notification via Telegram"""
    try:
        data = await request.json()
        title = data.get('title', 'إشعار')
        message = data.get('message')
        recipients = data.get('recipients', 'all')
        student_id = data.get('student_id')  # For specific student
        
        if not message:
            return {"success": False, "error": "الرسالة مطلوبة"}
        
        # Import telegram bot configuration
        from telegram import Bot
        from config.settings import settings
        
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        notification_text = f"🔔 **{title}**\n\n{message}"
        
        sent_count = 0
        
        if recipients == 'specific' and student_id:
            # Send to specific student
            try:
                await bot.send_message(
                    chat_id=student_id,
                    text=notification_text
                )
                
                # Save to database
                notification = Notification(
                    user_id=student_id,
                    title=title,
                    message=message,
                    type="admin",
                    read=False
                )
                await notification.insert()
                sent_count = 1
            except Exception as e:
                logger.error(f"Failed to send to {student_id}: {e}")
                return {"success": False, "error": f"فشل الإرسال: {str(e)}"}
                
        elif recipients == 'all':
            # Send to all registered users
            users = await User.find_all().to_list()
            
            for user in users:
                try:
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=notification_text
                    )
                    
                    # Save to database
                    notification = Notification(
                        user_id=user.telegram_id,
                        title=title,
                        message=message,
                        type="admin",
                        read=False
                    )
                    await notification.insert()
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to send to {user.telegram_id}: {e}")
                    
        return {
            "success": True, 
            "message": f"تم إرسال الإشعار إلى {sent_count} طالب"
        }
        
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        return {"success": False, "error": str(e)}


@app.get("/videos", response_class=HTMLResponse)
async def videos_list(request: Request, username: str = Depends(verify_admin)):
    """Videos management"""
    from database.models.video import Video
    
    videos = await Video.find().sort(-Video.uploaded_at).to_list()
    
    return templates.TemplateResponse("videos.html", {
        "request": request,
        "videos": videos,
        "username": username
    })


@app.get("/settings", response_class=HTMLResponse)
async def admin_settings(request: Request, username: str = Depends(verify_admin)):
    """Admin settings"""
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "username": username,
        "current_email": settings.ADMIN_USERNAME
    })


@app.post("/api/update-settings")
async def update_settings(request: Request, username: str = Depends(verify_admin)):
    """Update admin settings"""
    data = await request.json()
    # TODO: Implement settings update logic
    return {"status": "success", "message": "تم تحديث الإعدادات بنجاح"}


@app.get("/assignment/{assignment_id}/submissions", response_class=HTMLResponse)
async def assignment_submissions(
    request: Request,
    assignment_id: str,
    username: str = Depends(verify_admin)
):
    """View assignment submissions"""
    from database.models.assignment import Assignment
    
    assignment = await Assignment.find_one(Assignment.id == assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # Get user details for each submission
    submissions_with_users = []
    for submission in assignment.submissions:
        user = await User.find_one(User.telegram_id == int(submission.user_id))
        if user:
            submissions_with_users.append({
                "submission": submission,
                "user": user
            })
    
    return templates.TemplateResponse("assignment_submissions.html", {
        "request": request,
        "assignment": assignment,
        "submissions": submissions_with_users,
        "username": username,
        "bot_token": settings.TELEGRAM_BOT_TOKEN
    })


@app.post("/api/grade-submission")
async def grade_submission(request: Request, username: str = Depends(verify_admin)):
    """Grade a student's submission"""
    from database.models.assignment import Assignment
    
    data = await request.json()
    assignment_id = data.get("assignment_id")
    user_id = data.get("user_id")
    grade = int(data.get("grade", 0))
    feedback = data.get("feedback", "")
    
    assignment = await Assignment.find_one(Assignment.id == assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # Grade the submission
    await assignment.grade_submission(
        user_id=user_id,
        grade=grade,
        feedback=feedback,
        graded_by=username
    )
    
    # Send notification to student
    try:
        user = await User.find_one(User.telegram_id == int(user_id))
        if user:
            notification_text = f"""
🎓 **تم تصحيح واجبك!**

📝 الواجب: {assignment.title}
📊 الدرجة: {grade}/{assignment.max_grade}
📈 النسبة: {(grade/assignment.max_grade)*100:.1f}%

{'✅ مبروك! أنت ناجح 🎉' if grade >= assignment.pass_grade else '❌ للأسف لم تنجح. حاول مرة أخرى!'}
            """
            
            if feedback:
                notification_text += f"\n\n💬 **ملاحظات المدرس:**\n{feedback}"
            
            import httpx
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
                    json={
                        "chat_id": int(user_id),
                        "text": notification_text,
                        "parse_mode": "Markdown"
                    }
                )
            
            # Create notification record
            notification = Notification(
                user_id=int(user_id),
                title="تم تصحيح واجبك",
                message=f"حصلت على {grade}/{assignment.max_grade} في {assignment.title}",
                notification_type="grade",
                related_id=assignment_id
            )
            await notification.insert()
            
    except Exception as e:
        logger.error(f"Failed to send grade notification: {e}")
    
    logger.info(f"Assignment graded: {assignment.title} - User {user_id} - Grade {grade}")
    
    return {"status": "success", "message": "تم حفظ الدرجة بنجاح"}


@app.get("/student/{telegram_id}/grades", response_class=HTMLResponse)
async def student_grades(
    request: Request,
    telegram_id: int,
    username: str = Depends(verify_admin)
):
    """View student's grades"""
    from database.models.assignment import Assignment
    
    student = await User.find_one(User.telegram_id == telegram_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get all assignments with this student's submissions
    all_assignments = await Assignment.find().to_list()
    student_grades = []
    
    for assignment in all_assignments:
        submission = assignment.get_submission(str(telegram_id))
        if submission:
            student_grades.append({
                "assignment": assignment,
                "submission": submission
            })
    
    # Calculate statistics
    total_assignments = len(student_grades)
    graded_count = len([g for g in student_grades if g["submission"].status == "graded"])
    
    if graded_count > 0:
        total_grade = sum([g["submission"].grade for g in student_grades if g["submission"].grade])
        average_grade = total_grade / graded_count if graded_count > 0 else 0
    else:
        average_grade = 0
    
    return templates.TemplateResponse("student_grades.html", {
        "request": request,
        "student": student,
        "grades": student_grades,
        "total_assignments": total_assignments,
        "graded_count": graded_count,
        "average_grade": average_grade,
        "username": username
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
