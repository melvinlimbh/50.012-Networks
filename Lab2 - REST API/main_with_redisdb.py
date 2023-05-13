from fastapi import FastAPI, Response, Depends
from typing import Optional
from pydantic import BaseModel
import redis
import json

db = redis.Redis(host='redis', port='6379', db=0, decode_responses=True) # connect to localhost on port 6379
# r.set('foo', 'bar') sets a (key,value) pair
# r.get("foo") gets a value based on key, output = bar

class Student(BaseModel):
    name: str
    id: str
    gpa: int

#students = [{"name": "Alice","id": "1004803","gpa": 4.0},{ "name": "Bob", "id": "1004529","gpa": 3.6},{"name": "Charlie","id": "1004910","gpa": 5.0}, {"name": "K","id": "1004100","gpa": 1.5},{"name": "Cream","id": "1004233","gpa": 3.2}]
#"[{name:Alice, id:1004803, gpa: 4.0}|{name:Bob, id:1004529, gpa:3.6}|{name:Charlie, id: 1004910, gpa:5.0}|{name:K, id: 1004100, gpa: 1.5}|{name:Cream, id:1004233, gpa:3.2}]"
#"[{name:Alice, id:1004803, gpa: 4.0},{name:Bob, id:1004529, gpa:3.6},{name:Charlie, id: 1004910, gpa:5.0},{name:K, id: 1004100, gpa: 1.5},{name:Cream, id:1004233, gpa:3.2}]"

"""
app = fastAPI object instance
app.get("/PATH"), url = localhost:port_number/PATH
"""
app = FastAPI()

def all_students():
    students_json = db.get("students") # list of all students, but in json format
    students = json.loads(students_json) # list split nicely into students
    students_ls = []
    for _ in students: 
        # _ = details of 1 student : {"name":" \" 'Alice'\"","id":" \" '1004803'\"","gpa":4.0}
        name,id= _["name"],_["id"]
        index,index2 = name.find("\\",)+1, id.find("\\")+1
        full_name,studentID,grade = name[index:len(name)], id[index2:index2+8],_["gpa"]
       
        student = dict(name = full_name, id = studentID, gpa = grade)
        students_ls.append(student)

    return students_ls

def get_redis_client():
    return redis.Redis(host="redis")

@app.get("/") # no query
def home_page():
    return "MyPortal SUTD"

# @app.get("/students")
# def test():
#     all_students()
#     return json.dumps(all_students())

# @app.post("/students/test") # test bench
# def test(student: Student, response: Response ,redis_client: redis.Redis = Depends(get_redis_client)):
#     student_ls = all_students()

#     student = dict(name = student.name, id = student.id, gpa = float(student.gpa))
#             # "name": student.name,
#             # "id": student.id,
#             # "gpa" : student.gpa
#     for _ in student_ls:
#         student_id = _["id"][4:11]
#         if student_id == student["id"]:
#             response.status_code = 409
#             return f"student with id {student_id} id already exists"

#     student_ls.append(student)
#     response.status_code = 201

#     #update db
#     #db.set("students",json.dumps(students_ls))
    
#     return student_ls

@app.get("/students/{student_id}")
def find_student(student_id: str ,response: Response):
    students_ls = all_students()
    for student in students_ls:
        index = student["id"].find("1")
        studentID = student["id"][index:index+7]
        if studentID == student_id:
            return student
    response.status_code = 404
    return "student not found"

@app.get("/students&limit={limit}")
def count(limit:int):
    students = all_students()
    output = students[:limit]

    return output

# def sortBy(filter : str):
#     output =  sorted(students_ls,key = lambda d:d[filter])

#     return output

@app.get("/students")
def get_students(sortBy: Optional[str] = None, limit: Optional[int] = None, 
                    offset: Optional[int] = None):

    students_ls = all_students()
    output = students_ls

    if sortBy:
        output = sorted(students_ls,key = lambda d:d[sortBy])
    
    if limit:
        output = output[:limit]

    if offset:
        output = output[::offset+1]

    return output


@app.post("/students")
def create_student(student: Student, response: Response ,redis_client: redis.Redis = Depends(get_redis_client)):
    students_ls = db.get("students")
    student = dict(name = student.name, id = student.id, gpa = float(student.gpa))

    for _ in students_ls:
        studentID = _["id"]
        if studentID == student["id"]:
            response.status_code = 409
            return f"student with id {studentID} id already exists"

    students_ls.append(student) #all good
    test = json.dumps(students_ls)
    response.status_code = 201

    #update db
    db.set('students',test)

@app.delete("/students/{student_id}")
def delete_students(student_id: str ,response: Response):

    students_ls = all_students()
    for i,student in enumerate(students_ls):
        index = student["id"].find("1")
        studentID = student["id"][index:index+7]
        if studentID == student_id:
            students_ls.pop(i)
            db.set("students",json.dumps(students_ls))
    response.status_code = 404
    return "student not found"