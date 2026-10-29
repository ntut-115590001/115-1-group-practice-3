"""F2: Class Conflict and Course Enrollment Checks. 多層次衝堂與選課檢查"""

from data_management import students, courses, classes, format_time, enrolled_count
from src.cli import command

## 目前已選課程 already enrolled courses and sections
def get_enrolledinfo(student_id):
    enrolled_courses = []
    enrolled_sections = []
    current_credit = 0
    for course_id in students[student_id].course_ids:
        course = courses[course_id]
        current_credit += course.credit
        for time, room in course.sections:
            enrolled_courses.append((course_id, course.name))
            enrolled_sections.append(time)
    
    return current_credit, enrolled_courses, enrolled_sections


## 時段衝堂 section conflict check
def check_section_conflict(desired_section, enrolled_courses, enrolled_sections):
    section_conflict = []
    for i in range(len(enrolled_sections)): #checks each list of enrolled_sections
        for p in enrolled_sections[i]: #each value in sections[i]. day1period1, day1period2 
            for times, room in desired_section:
                if p in times: #desired_section taken?
                    conflict = [format_time(p), enrolled_courses[i]]
                    
                    if conflict not in section_conflict:
                        section_conflict.append(conflict)

    return section_conflict


## 學分限制 credit limit check
def check_credit_limit(student_info, current_credit, desired_credit):
    credit_conflict = False
    student_class_id = student_info.class_ids[0]
    student_class = classes[student_class_id]
    if current_credit + desired_credit > student_class.credit_limit:
        credit_conflict = True

    return credit_conflict, student_class


## 人數限制 student limit check 
def check_student_limit(desired_course, desired_courseid):
    stu_limit_conflict = False
    if desired_course.student_limit - enrolled_count(desired_courseid) <= 0:
        stu_limit_conflict = True

    return stu_limit_conflict


@command('student_addCourse')
def student_addCourse():
    student_id = input("學號: ")
    desired_courseid = input("欲加選: ")
    student_info = students[student_id]
    desired_course = courses[desired_courseid]
    desired_section = desired_course.sections
    desired_credit = desired_course.credit

    current_credit, enrolled_courses, enrolled_sections = get_enrolledinfo(student_id)
   
    section_conflict = check_section_conflict(desired_section, enrolled_courses, enrolled_sections)
    credit_conflict, student_class = check_credit_limit(student_info, current_credit, desired_credit)
    stu_limit_conflict = check_student_limit(desired_course, desired_courseid)

    ## 選課結果 result
    if section_conflict != [] or credit_conflict == True or stu_limit_conflict == True:
        issue_number = 0
        print("選課結果：失敗")

        if section_conflict != []:
            for i in section_conflict:
                issue_number += 1
                print("衝突", issue_number, "：", i[0])
                print("已選課程：", i[1])
        if credit_conflict == True:
            issue_number += 1
            print("衝突", issue_number, "：加選後總學分超過上限")         
        if stu_limit_conflict == True:
            issue_number += 1
            print("衝突", issue_number, "：加選課程已額滿")
    
    else:
        print("選課結果：成功")

    print("目前學分：", current_credit)
    print("加選後學分：", current_credit + desired_credit)
    print("學分上限：", student_class.credit_limit)
