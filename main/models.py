from django.db import models
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver


class Subject(models.Model):
    name = models.CharField(max_length=255)
    
    def __str__(self):
        return self.name


class Teacher(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    photo = models.ImageField(upload_to='teacher_photos/', blank=True, null=True)
    is_class_teacher = models.BooleanField(default=False)
    subjects = models.ManyToManyField(Subject, blank=True) 
    classes = models.ManyToManyField('Class', related_name='teaching_classes', blank=True)  


    def save(self, *args, **kwargs):
        if not self.password_hash.startswith('pbkdf2'):
            self.password_hash = make_password(self.password_hash)
        super().save(*args, **kwargs)


    def __str__(self):
        return self.full_name


class Class(models.Model):
    CLASSES = [
 ('1А', '1А'),
        ('1Б', '1Б'),
        ('1В', '1В'),
        ('1Г', '1Г'),
        ('2А', '2А'),
        ('2Б', '2Б'),
        ('2В', '2В'),
        ('2Г', '2Г'),
        ('3А', '3А'),
        ('3Б', '3Б'),
        ('3В', '3В'),
        ('3Г', '3Г'),
        ('4А', '4А'),
        ('4Б', '4Б'),
        ('4В', '4В'),
        ('4Г', '4Г'),
        ('5А', '5А'),
        ('5Б', '5Б'),
        ('5В', '5В'),
        ('11А', '11А'),
        ('11Б', '11Б'),
        ('11В', '11В'),
        ('11Г', '11Г'),
    ]

    name = models.CharField(max_length=50, choices=CLASSES) 
    class_teacher = models.OneToOneField(
        Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='class_teacher_of')

    def __str__(self):
        return self.name


class Student(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=128)
    class_id = models.ForeignKey(Class, on_delete=models.CASCADE) 
    photo = models.ImageField(upload_to='student_photos/', blank=True, null=True)
    

    def save(self, *args, **kwargs):
        if not self.password_hash.startswith('pbkdf2'):
            self.password_hash = make_password(self.password_hash)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.class_id})"


@receiver(post_save, sender=Student)
def fill_student_subjects(sender, instance, created, **kwargs):
    if created:
        subjects = ClassSubject.objects.filter(class_id=instance.class_id)
        for subject in subjects:
            StudentSubject.objects.get_or_create(
                student=instance,
                subject=subject.subject
            )



class ClassSubject(models.Model):
    class_id = models.ForeignKey(Class, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('class_id', 'subject')


@receiver(post_save, sender=ClassSubject)
def update_students_subjects(sender, instance, created, **kwargs):
    if created:
        students = Student.objects.filter(class_id=instance.class_id)
        for student in students:            
            StudentSubject.objects.get_or_create(student=student, subject=instance.subject)



class StudentSubject(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('student', 'subject')  

class Grade(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    grade = models.IntegerField(null=True, blank=True)
    date = models.DateField()
  
    class Meta:
        unique_together = ('student', 'subject', 'date')


class GradeLog(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    grade = models.IntegerField(null=True, blank=True)
    date = models.DateField()
    updated_at = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=10, choices=[('created', 'Створено'), ('updated', 'Оновлено')])

    class Meta:
        ordering = ['-updated_at']
