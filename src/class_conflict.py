"""F2: Class Conflict and Course Enrollment Checks. 多層次衝堂與選課檢查"""

from data_management import students, courses, classes, format_time, enrolled_count

student_id = input("學號: ")
desired_courseid = input("欲加選: ")
student_info = students[student_id]
desired_course = courses[desired_courseid]
desired_section = desired_course.sections
desired_credit = desired_course.credit

## 目前已選課程 already enrolled courses and sections
enrolled_courses = []
enrolled_sections = []
current_credit = 0
for course_id in students[student_id].course_ids:
    course = courses[course_id]
    current_credit += course.credit
    for time, room in course.sections:
        enrolled_courses.append((course_id, course.name))
        enrolled_sections.append(time)

## 時段衝堂 section conflict check
issue_number = 0
for i in range(len(enrolled_sections)): #checks each list of enrolled_sections
    for p in enrolled_sections[i]: #each value in sections[i]. day1period1, day1period2 
        for times, room in desired_section:
            if p in times: #desired_section taken?
                issue_number += 1
                p = format_time(p)
                print("衝突", issue_number, "：", p)
                print("已選課程：", enrolled_courses[i])
                break

## 學分限制 credit limit check
student_class_id = student_info.class_ids[0]
student_class = classes[student_class_id]
if current_credit + desired_credit > student_class.credit_limit:
    issue_number += 1
    print("衝突", issue_number, "：加選後總學分超過上限")         

## 人數限制 student limit check 
if desired_course.student_limit - enrolled_count(desired_courseid) <= 0:
    issue_number += 1
    print("衝突", issue_number, "：加選課程已額滿")

## 選課結果 result 
if issue_number > 0:
    print("選課結果：失敗")
else:
    print("選課結果：成功")

print("目前學分：", current_credit)
print("加選後學分：", current_credit + desired_credit)
print("學分上限：", student_class.credit_limit)
