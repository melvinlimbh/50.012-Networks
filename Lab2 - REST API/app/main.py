from fastapi import FastAPI, Response, Depends
from typing import Optional
from pydantic import BaseModel

class Student(BaseModel):
    name: str
    id: str
    gpa: Optional[int] = None

students = [
    {"name": "Alice","id": "1004803","gpa": 4.0},
    { "name": "Bob", "id": "1004529","gpa": 3.6},
    {"name": "Charlie","id": "1004910","gpa": 5.0}, 
    {"name": "K","id": "1004100","gpa": 1.5},
    {"name": "Cream","id": "1004233","gpa": 3.2}
    ]


"""
app = fastAPI object instance
app.get("/PATH"), url = localhost:port_number/PATH
"""
app = FastAPI()

@app.get("/") # no query
def home_page():
    return "MyPortal SUTD"

@app.get("/students/{student_id}")
def find_student(student_id: str ,response: Response):
    global students
    for student in students:
        if student["id"] == student_id:
            return student

    response.status_code = 404
    return "student not found"

@app.get("/students&limit={limit}")
def count(limit:int):
    global students
    output = students[:limit]

    return output

@app.get("/students")
def get_students(sortBy: Optional[str] = None, limit: Optional[int] = None, 
                    offset: Optional[int] = None):
    global students
    output = students

    if sortBy:
        output = sorted(output,key = lambda d:d[sortBy])
    
    if limit:
        output = output[:limit]

    if offset:
        output = output[::offset+1]

    return output


@app.post("/students")
def create_student(student: Student, response: Response):
    global students

    if not student.name: 
        response.status_code = 400
        return "Missing name."
    elif not student.id:
        response.status_code = 400
        return "Missing student id."
    elif student.id[:3] != "100" or len(student.id) != 7:
        response.status_code = 400
        return "Wrong student id format."
    elif student.gpa == None:
        return "N"

    student = dict(name = student.name, id = student.id, gpa = float(student.gpa))
    for exist in students:
        studentID = exist["id"]
        if studentID == student["id"]:
            response.status_code = 409
            return f"student with id {studentID} already exists"

    students.append(student)
    return f"\n Student {studentID} added successfully. =>\n",students


@app.delete("/students/delete/{student_id}")
def delete_students(student_id:str ,response: Response):
    global students
    if not student_id.isdigit():
        return "Please enter student id number only"

    for i,student in enumerate(students): 
        studentID = student["id"]
        if studentID == student_id:
            students.pop(i)
            return f"Student {studentID} deleted",students

    response.status_code = 404
    return "student not found"

@app.delete("/students/batch_delete/{key}{condition}{value}")
def batch_delete(key:str,condition,value:int):
    global students
    output = students
    if condition == "<":
        for student in output:
            student_id = student["id"]
            if student[key] < value:
                delete_students(student_id,response=Response)

    return f"Batch delete of {key} {condition} {value} done.",output