from main.models import Student, ClassSubject, StudentSubject

def add_subjects_to_existing_students():
    students = Student.objects.all()
    total = students.count()
    print(f"Всего учеников: {total}")

    for i, student in enumerate(students, start=1):
        subjects = ClassSubject.objects.filter(class_id=student.class_id)
        for class_subject in subjects:
            StudentSubject.objects.get_or_create(student=student, subject=class_subject.subject)
        print(f"Обработан ученик {i} из {total}: {student}")
