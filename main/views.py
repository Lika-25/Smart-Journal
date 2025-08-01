from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db import transaction
from django.db.utils import IntegrityError
from django.db.models import Avg

from datetime import datetime
import random, string
import io, base64

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from .forms import EmailForm, RegistrationForm, VerificationCodeForm, NewPasswordForm, TeacherRegistrationForm
from .models import Student, Class, Teacher, Subject, StudentSubject, Grade, ClassSubject, GradeLog



# Create your views here.


def index(request):
    return render(request, 'main/index.html',
    {'title': 'Головна сторінка сайту'})


def chose_role(request):
    return render(request, 'main/chose_role.html')

def logout_view(request):
    # Завершаем сессию
    logout(request)
    # Перенаправляем на главную страницу
    return redirect('main')


def teacher_profile(request):
    teacher = request.user  
    return render(request, 'main/teacher_profile.html', {'teacher': teacher})


def student_profile(request):
    student = request.user  
    return render(request, 'main/student_profile.html', {'student': student})


def register_teacher(request):
    return render(request, 'main/register_teacher.html')


def teacher_subjects(request):
    return render(request, 'main/teacher_subjects.html')


def teacher_students(request):
    return render(request, 'main/teacher_students.html')


def teacher_class(request):
    return render(request, 'main/teacher_class.html')


def student_grades(request):
    return render(request, 'main/student_grades.html')


def student_class(request):
    return render(request, 'main/student_class.html')


def student_notifications(request):
    return render(request, 'main/student_notifications.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        # Шукаємо вчителя
        try:
            user = Teacher.objects.get(email=email)
            if check_password(password, user.password_hash):
                request.session['user_id'] = user.id
                request.session['role'] = 'teacher'
                request.session['is_class_teacher'] = user.is_class_teacher  
                return redirect('teacher_profile')
        except Teacher.DoesNotExist:
            pass

        # Шукаємо учня
        try:
            user = Student.objects.get(email=email)
            if check_password(password, user.password_hash):
                request.session['user_id'] = user.id
                request.session['role'] = 'student'
                return redirect('student_profile')
        except Student.DoesNotExist:
            pass

        # Якщо нічого не знайшли
        return render(request, 'main/login.html', {'error': 'Невірні дані для входу!'})

    return render(request, 'main/login.html')

def generate_verification_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def register_student(request):
    if request.method == 'POST':
        if 'email' in request.POST and 'verification_code' not in request.POST and 'password1' not in request.POST:
            # Шаг 1: введено email — отправляем код
            email = request.POST.get('email')

            # 🔎 Перевірка, чи існує вже така пошта
            if Student.objects.filter(email=email).exists():
                messages.error(request,
                               "Ця електронна пошта вже зареєстрована.")
                return render(request, 'main/register_student.html', {
                    'step': 'email',
                    'form': EmailForm()
                })

            code = generate_verification_code()
            request.session['verification_code'] = code
            request.session['email'] = email

            send_mail(
                'Код підтвердження для реєстрації',
                f'Ваш код підтвердження: {code}',
                'kapiba@ukr.net',  # От кого
                [email],
                fail_silently=False,
            )
            messages.info(
                request,
                'Код підтвердження надіслано на вашу електронну пошту.')
            return render(request, 'main/register_student.html', {
                'step': 'verification',
                'email': email
            })

        elif 'verification_code' in request.POST:
            # Шаг 2: проверка кода
            entered_code = request.POST.get('verification_code')
            actual_code = request.session.get('verification_code')
            email = request.session.get('email')

            if entered_code == actual_code:
                # Показ формы регистрации с классами
                form = RegistrationForm(initial={'email': email})
                classes = Class.objects.all()
                return render(
                    request,
                    'main/register_student.html',
                    {
                        'form': form,
                        'step': 'register',
                        'classes': classes,  # Щоб рендерити список
                    })
            else:
                messages.error(request, 'Невірний код підтвердження')
                return redirect('register_student')

        elif 'password1' in request.POST:
            # Шаг 3: регистрация
            form = RegistrationForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                request.session.pop('verification_code', None)
                request.session.pop('email', None)
                # Очистка всех сессионных данных, если они есть
                request.session.pop('step', None)
                request.session.pop('reset_email', None)
                request.session.pop('reset_code', None)
                messages.success(request, 'Реєстрація успішна!')
                return redirect('login')
            else:
                messages.error(request, 'Помилка при збереженні даних!')
                classes = Class.objects.all()
                return render(request, 'main/register_student.html', {
                    'form': form,
                    'step': 'register',
                    'classes': classes,
                })


    else:
        form = EmailForm()
        return render(request, 'main/register_student.html', {
            'form': form,
            'step': 'email'
        })
    


def set_new_password(request):
    form = None
    if request.method == 'GET':
        if not request.session.get('just_sent_code') and not request.session.get('just_verified'):
            # справжній новий вхід
            request.session.pop('reset_email', None)
            request.session.pop('reset_code', None)
            request.session.pop('user_type', None)
            request.session['step'] = 'email'

    step = request.session.get('step', 'email')
    print(f"[DEBUG] step before handling: {step}, just_sent_code={request.session.get('just_sent_code')}, just_verified={request.session.get('just_verified')}")

    if request.method == 'POST':
        if step == 'email':
            form = EmailForm(request.POST)
            if form.is_valid():
                email = form.cleaned_data['email']
                user_type = None
                try:
                    user = Student.objects.get(email=email)
                    user_type = 'student'
                except Student.DoesNotExist:
                    try:
                        user = Teacher.objects.get(email=email)
                        user_type = 'teacher'
                    except Teacher.DoesNotExist:
                        messages.error(request, "Користувача з такою поштою не знайдено.")
                        return redirect('register_student')

                code = generate_verification_code()
                request.session['reset_email'] = email
                request.session['reset_code'] = code
                request.session['user_type'] = user_type
                request.session['step'] = 'verification'
                request.session['just_sent_code'] = True

                send_mail(
                    subject="Код для зміни пароля",
                    message=f"Ваш код підтвердження: {code}",
                    from_email="kapiba@ukr.net",
                    recipient_list=[email],
                    fail_silently=False
                )
                messages.info(request, 'Код підтвердження надіслано.')
                return redirect('set_new_password')

        elif step == 'verification':
            form = VerificationCodeForm(request.POST)
            if form.is_valid():
                entered = form.cleaned_data['verification_code']
                actual = request.session.get('reset_code')
                if entered == actual:
                    request.session['step'] = 'new_password'
                    request.session['just_verified'] = True
                    return redirect('set_new_password')
                else:
                    messages.error(request, "Неправильний код підтвердження.")

        elif step == 'new_password':
            form = NewPasswordForm(request.POST)
            if form.is_valid():
                new_pass = form.cleaned_data['password1']
                email = request.session.get('reset_email')
                user_type = request.session.get('user_type')

                if user_type == 'student':
                    user = Student.objects.get(email=email)
                else:
                    user = Teacher.objects.get(email=email)

                if check_password(new_pass, user.password_hash):
                    form.add_error('password1', "Новий пароль не може співпадати зі старим. Придумайте інший.")
                else:
                    user.password_hash = make_password(new_pass)
                    user.save()
                    request.session.flush()
                    messages.success(request, "Пароль успішно змінено.")
                    return redirect('login')

            else:
                messages.error(request, "Будь ласка, виправте помилки в формі.")

    if request.method == 'GET':
        if step == 'email':
            form = EmailForm()
        elif step == 'verification':
            form = VerificationCodeForm()
        elif step == 'new_password':
            form = NewPasswordForm()

        request.session.pop('just_sent_code', None)
        request.session.pop('just_verified', None)

    print(f"[DEBUG] step after handling: {request.session.get('step')}")
    return render(request, 'main/set_new_password.html', {
        'form': form,
        'step': step,
        'email': request.session.get('reset_email')
    })


def register_teacher(request):
    if request.method == 'POST':
        # КРОК 1: Введено email — надсилаємо код підтвердження
        if 'email' in request.POST and 'verification_code' not in request.POST and 'password1' not in request.POST:
            email = request.POST.get('email')

            if Student.objects.filter(email=email).exists() or Teacher.objects.filter(email=email).exists():
                messages.error(request, "Ця електронна пошта вже зареєстрована.")
                return render(request, 'main/register_teacher.html', {
                    'step': 'email',
                    'form': EmailForm()
                })

            code = generate_verification_code()
            request.session['verification_code'] = code
            request.session['email'] = email

            send_mail(
                'Код підтвердження для реєстрації викладача',
                f'Ваш код підтвердження: {code}',
                'kapiba@ukr.net',
                [email],
                fail_silently=False,
            )
            messages.info(request, 'Код підтвердження надіслано на вашу пошту.')
            return render(request, 'main/register_teacher.html', {
                'step': 'verification',
                'email': email
            })

        # КРОК 2: Перевірка коду
        elif 'verification_code' in request.POST:
            entered_code = request.POST.get('verification_code')
            actual_code = request.session.get('verification_code')
            email = request.session.get('email')

            if entered_code == actual_code:
                form = TeacherRegistrationForm(initial={'email': email})
                return render(request, 'main/register_teacher.html', {
                    'form': form,
                    'step': 'register',
                    'subjects': Subject.objects.all(),
                    'classes': Class.objects.all(),
                })
            else:
                messages.error(request, 'Невірний код підтвердження')
                return redirect('register_teacher')

        # КРОК 3: Реєстрація
        elif 'password1' in request.POST:
            form = TeacherRegistrationForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                request.session.pop('verification_code', None)
                request.session.pop('email', None)
                messages.success(request, 'Реєстрація пройшла успішно!')
                return redirect('login')
            else:
                messages.error(request, 'Помилка при збереженні форми.')
                return render(request, 'main/register_teacher.html', {
                    'form': form,
                    'step': 'register',
                    'subjects': Subject.objects.all(),
                    'classes': Class.objects.all(),
                })

    else:
        form = EmailForm()
        return render(request, 'main/register_teacher.html', {
            'form': form,
            'step': 'email'
        })
    



def student_profile(request):
    if request.session.get('role') != 'student' or not request.session.get('user_id'):
        return redirect('login') 

    student_id = request.session['user_id']
    student = Student.objects.get(id=student_id)
    subjects = StudentSubject.objects.filter(student=student).select_related('subject')

    return render(request, 'main/student_profile.html', {
        'student': student,
        'subjects': subjects
    })

def update_student_profile(request):
    if request.method == 'POST':
        if request.session.get('role') != 'student' or not request.session.get('user_id'):
            return redirect('login')

        student = Student.objects.get(id=request.session['user_id'])

        full_name = request.POST.get('full_name')
        email = request.POST.get('email') 
        photo = request.FILES.get('photo')

        if full_name:
            student.full_name = full_name
        if email:
            student.email = email
        if photo:
            student.photo = photo
        student.save()

    return redirect('student_profile')


def student_class(request):
    if request.session.get('role') != 'student' or not request.session.get('user_id'):
        return redirect('login')

    student_id = request.session['user_id']
    student = Student.objects.select_related('class_id__class_teacher').get(id=student_id)
    classmates = Student.objects.filter(class_id=student.class_id).order_by('full_name')
    teacher = student.class_id.class_teacher
    teacher_subjects = teacher.subjects.all() if teacher else []

    ranked_students = (
        Student.objects
        .filter(class_id=student.class_id)
        .annotate(average_score=Avg('grade__grade'))
        .order_by('-average_score')
    )
    stats = (
        Grade.objects.filter(student__in=classmates)
        .values('student__id', 'student__full_name')
        .annotate(avg_grade=Avg('grade'))
        .order_by('-avg_grade')
    )
    stats_chart = generate_stats_bar_chart(stats)

    return render(request, 'main/student_class.html', {
        'student': student,
        'classmates': classmates,
        'teacher': teacher,
        'teacher_subjects': teacher_subjects,
        'ranked_students': ranked_students,
        'stats_chart': stats_chart,
    })


def generate_grade_chart(grades):
    if not grades:
        return None

    grades = grades.order_by('date')
    dates = [g.date.strftime('%d.%m') for g in grades]
    values = [g.grade for g in grades]
    width = min(max(len(dates) * 0.6, 6), 15)
    height = 4

    fig, ax = plt.subplots(figsize=(width, height))
    ax.plot(dates, values, marker='o', linestyle='-', color='blue')

    ax.set_title('Динаміка оцінок')
    ax.set_xlabel('Дата')
    ax.set_ylabel('Оцінка')

    ax.set_ylim(0, 12)
    ax.set_yticks(range(0, 13))

    plt.xticks(rotation=45)
    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    chart_data = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close(fig)
    return chart_data




def student_grades(request):
    if request.session.get('role') != 'student' or not request.session.get('user_id'):
        return redirect('login')

    student_id = request.session['user_id']
    student = Student.objects.select_related('class_id').get(id=student_id)

    student_subjects = StudentSubject.objects.filter(student=student).select_related('subject')
    subjects = [ss.subject for ss in student_subjects]
    classmates = Student.objects.filter(class_id=student.class_id)

    for subject in subjects:
        marks = Grade.objects.filter(student=student, subject=subject).order_by('-date')
        subject.marks = marks

        subject.ranking = (
            Grade.objects
            .filter(student__in=classmates, subject=subject)
            .values('student__id', 'student__full_name')
            .annotate(average=Avg('grade'))
            .order_by('-average')
        )
        class_subj = ClassSubject.objects.filter(class_id=student.class_id, subject=subject).select_related('teacher').first()
        subject.teacher = class_subj.teacher if class_subj else None
        subject.chart = generate_grade_chart(marks)

    return render(request, 'main/student_grades.html', {
        'student': student,
        'subjects': subjects,
    })



def teacher_profile(request):
    if request.session.get('role') != 'teacher' or not request.session.get('user_id'):
        return redirect('login')

    teacher = Teacher.objects.get(id=request.session['user_id'])
    class_teacher_class = None
    if teacher.is_class_teacher:
        class_teacher_class = teacher.class_teacher_of 

    class_subjects = ClassSubject.objects.filter(teacher=teacher).select_related('class_id', 'subject')

    subjects_classes = {}
    for cs in class_subjects:
        if cs.subject.name not in subjects_classes:
            subjects_classes[cs.subject.name] = []
        subjects_classes[cs.subject.name].append(cs.class_id.name)

    return render(request, 'main/teacher_profile.html', {
        'teacher': teacher,
        'class_teacher_class': class_teacher_class,
        'subjects_classes': subjects_classes,
    })

def update_teacher_profile(request):
    if request.method == 'POST':
        if request.session.get('role') != 'teacher' or not request.session.get('user_id'):
            return redirect('login')

        teacher = Teacher.objects.get(id=request.session['user_id'])

        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        photo = request.FILES.get('photo')

        if full_name:
            teacher.full_name = full_name
        if email:
            teacher.email = email
        if photo:
            teacher.photo = photo
        teacher.save()

    return redirect('teacher_profile')


def generate_stats_bar_chart(stats):
    if not stats:
        return None

    names = [entry['student__full_name'] for entry in stats]
    averages = [entry['avg_grade'] for entry in stats]
    fig, ax = plt.subplots(figsize=(max(len(stats) * 0.8, 6), 5))
    bars = ax.bar(names, averages, color='skyblue')
    ax.set_ylim(0, 12)
    ax.set_ylabel('Середній бал')
    ax.set_title('Графік середнього балу учнів')
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=45, ha='right', fontsize=8, wrap=True)
    ax.yaxis.set_ticks([i for i in range(0, 13)])

    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height + 0.2,
                f'{height:.2f}', ha='center', va='bottom', fontsize=8)

    fig.subplots_adjust(bottom=0.3)

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight') 
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close(fig)
    return image_base64



def teacher_class(request):
    teacher_id = request.session.get('user_id')
    role = request.session.get('role')

    if role != 'teacher':
        return redirect('login')

    teacher = Teacher.objects.get(id=teacher_id)

    if not teacher.is_class_teacher or not hasattr(teacher, 'class_teacher_of'):
        return render(request, 'main/teacher_class.html', {'not_class_teacher': True})

    class_obj = teacher.class_teacher_of
    students = Student.objects.filter(class_id=class_obj).order_by('full_name')

    stats = (
        Grade.objects.filter(student__in=students)
        .values('student__id', 'student__full_name')
        .annotate(avg_grade=Avg('grade'))
        .order_by('-avg_grade')
    )

    stats_chart = generate_stats_bar_chart(stats)

    return render(request, 'main/teacher_class.html', {
        'class_obj': class_obj,
        'students': students,
        'stats': stats,
        'stats_chart': stats_chart,
    })



def teacher_grades(request):
    teacher_id = request.session.get('user_id')
    role = request.session.get('role')

    if role != 'teacher':
        return redirect('login')

    try:
        teacher = Teacher.objects.get(id=teacher_id)
    except Teacher.DoesNotExist:
        return redirect('login')

    subjects = Subject.objects.filter(classsubject__teacher=teacher).distinct()
    selected_subject_id = request.GET.get('subject')
    selected_class_id = request.GET.get('class')

    students = []
    grades_by_student = {}
    dates = []
    classes = []

    if selected_subject_id:
        classes = Class.objects.filter(
            classsubject__subject_id=selected_subject_id,
            classsubject__teacher=teacher
        ).distinct()
    
    ranking = []
    if selected_subject_id and selected_class_id:
        students = Student.objects.filter(class_id=selected_class_id).order_by('full_name')

        grades_by_student = {
            student.id: {
                grade.date: grade.grade
                for grade in Grade.objects.filter(student=student, subject_id=selected_subject_id)
            }
            for student in students
        }

        dates = list(Grade.objects.filter(
            subject_id=selected_subject_id,
            student__class_id=selected_class_id
        ).values_list('date', flat=True).distinct())
        dates.sort()

        

        student_avg_grades = Grade.objects.filter(
        subject_id=selected_subject_id,
        student__class_id=selected_class_id,
        grade__isnull=False
        ).values('student_id').annotate(avg_grade=Avg('grade'))

        student_avg_map = {entry['student_id']: round(entry['avg_grade'], 2) for entry in student_avg_grades}

        ranking = sorted(
            ((student, student_avg_map.get(student.id)) for student in students),
            key=lambda x: x[1] if x[1] is not None else 0,
            reverse=True
        )


    if request.method == 'POST':
        if 'add_date' in request.POST:
            new_date_str = request.POST.get('new_date')
            if new_date_str:
                try:
                    new_date = datetime.strptime(new_date_str, '%Y-%m-%d').date()
                    if new_date not in dates:
                        with transaction.atomic():
                            for student in students:
                                Grade.objects.get_or_create(
                                    student=student,
                                    subject_id=selected_subject_id,
                                    date=new_date,
                                    defaults={'grade': None}
                                )
                    return redirect(f'{request.path}?subject={selected_subject_id}&class={selected_class_id}')
                except ValueError:
                    return HttpResponseBadRequest("Невірний формат дати.")

        elif 'delete_date' in request.POST:
            delete_date_str = request.POST.get('delete_date')
            try:
                delete_date = datetime.strptime(delete_date_str, '%Y-%m-%d').date()
                Grade.objects.filter(
                    subject_id=selected_subject_id,
                    student__class_id=selected_class_id,
                    date=delete_date
                ).delete()
                return redirect(f'{request.path}?subject={selected_subject_id}&class={selected_class_id}')
            except ValueError:
                return HttpResponseBadRequest("Невірний формат дати.")

        elif 'save_grades' in request.POST:
            try:
                with transaction.atomic():
                    for student in students:
                        for date in dates:
                            key = f'grade_{student.id}_{date.strftime("%Y-%m-%d")}'
                            value = request.POST.get(key)

                            if value and value.strip():
                                new_grade = int(value)
                                grade_obj, created = Grade.objects.update_or_create(
                                    student=student,
                                    subject_id=selected_subject_id,
                                    date=date,
                                    defaults={'grade': new_grade}
                                )

                                # 🔁 Добавляем запись в журнал логов
                                GradeLog.objects.create(
                                    student=student,
                                    subject_id=selected_subject_id,
                                    teacher=teacher,
                                    grade=new_grade,
                                    date=date,
                                    action='created' if created else 'updated'
                                )
                            else:
                                Grade.objects.filter(
                                    student=student,
                                    subject_id=selected_subject_id,
                                    date=date
                                ).delete()

                return redirect(f'{request.path}?subject={selected_subject_id}&class={selected_class_id}')
            except (IntegrityError, ValueError):
                return HttpResponseBadRequest("Помилка при збереженні оцінок.")

    return render(request, 'main/teacher_grades.html', {
        'subjects': subjects,
        'classes': classes,
        'students': students,
        'grades_by_student': grades_by_student,
        'ranking': ranking,  
        'dates': dates,
        'selected_subject_id': int(selected_subject_id) if selected_subject_id else None,
        'selected_class_id': int(selected_class_id) if selected_class_id else None,
       
    })


def student_notifications(request):
    student_id = request.session.get('user_id')
    role = request.session.get('role')

    if role != 'student':
        return redirect('login')

    logs = GradeLog.objects.filter(student_id=student_id).select_related('teacher', 'subject').order_by('-updated_at')[:50]

    return render(request, 'main/student_notifications.html', {
        'logs': logs
    })