from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import random
import uuid
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Math Exam API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Option(BaseModel):
    value: float
    text: str

class Question(BaseModel):
    id: str
    question_text: str
    operation: str
    options: List[Option]
    correct_answer: float
    user_answer: Optional[float] = None

class Exam(BaseModel):
    id: str
    questions: List[Question]
    total_questions: int
    completed: bool = False
    score: Optional[float] = None

exams = {}

def generate_options(correct_answer: float, operation: str) -> List[Option]:
    options = []
    
    # Add correct answer
    options.append(Option(value=correct_answer, text=str(correct_answer)))
    
    # Generate wrong options
    used_values = {correct_answer}
    while len(options) < 4:
        if operation in ['+', '-']:
            wrong_answer = correct_answer + random.choice([-2, -1, 1, 2])
        else:  # '*' operation
            wrong_answer = correct_answer + random.choice([-3, -2, 2, 3])
            
        if wrong_answer not in used_values and wrong_answer > 0:
            used_values.add(wrong_answer)
            options.append(Option(value=wrong_answer, text=str(wrong_answer)))
    
    # Shuffle options
    random.shuffle(options)
    return options

def generate_question() -> Question:
    # Use simpler operations
    operations = ["+", "-", "*"]
    operation = random.choice(operations)
    
    # Generate simpler numbers
    if operation in ['+', '-']:
        num1 = random.randint(1, 20)
        num2 = random.randint(1, 10)
    else:  # multiplication
        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
    
    # Calculate correct answer
    if operation == "+":
        correct_answer = num1 + num2
        operation_name = "addition"
    elif operation == "-":
        # Ensure positive result
        if num1 < num2:
            num1, num2 = num2, num1
        correct_answer = num1 - num2
        operation_name = "subtraction"
    else:  # multiplication
        correct_answer = num1 * num2
        operation_name = "multiplication"
    
    question_text = f"What is {num1} {operation} {num2}?"
    
    return Question(
        id=str(uuid.uuid4()),
        question_text=question_text,
        operation=operation_name,
        options=generate_options(correct_answer, operation),
        correct_answer=correct_answer
    )

@app.post("/create-exam")
async def create_exam(num_questions: int = 10):
    """Create a new exam with specified number of questions"""
    exam_id = str(uuid.uuid4())
    questions = [generate_question() for _ in range(num_questions)]
    
    exam = Exam(
        id=exam_id,
        questions=questions,
        total_questions=num_questions
    )
    
    exams[exam_id] = exam
    return {"exam_id": exam_id, "exam": exam}

@app.post("/submit-answer/{exam_id}/{question_id}")
async def submit_answer(exam_id: str, question_id: str, answer: float):
    """Submit an answer for a specific question"""
    if exam_id not in exams:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    exam = exams[exam_id]
    question = next((q for q in exam.questions if q.id == question_id), None)
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    question.user_answer = answer
    return {"correct": question.correct_answer == answer}

@app.post("/complete-exam/{exam_id}")
async def complete_exam(exam_id: str):
    """Complete the exam and get the final score"""
    if exam_id not in exams:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    exam = exams[exam_id]
    correct_answers = sum(
        1 for q in exam.questions
        if q.user_answer is not None and q.correct_answer == q.user_answer
    )
    
    exam.completed = True
    exam.score = (correct_answers / exam.total_questions) * 100
    
    return {
        "completed": True,
        "score": exam.score,
        "total_questions": exam.total_questions,
        "correct_answers": correct_answers,
        "questions": exam.questions  # Return questions to show correct answers
    }

@app.get("/exam/{exam_id}")
async def get_exam(exam_id: str):
    """Get exam details"""
    if exam_id not in exams:
        raise HTTPException(status_code=404, detail="Exam not found")
    return exams[exam_id]