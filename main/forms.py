from django import forms
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from .models import Student, Class, Teacher, Subject, ClassSubject, StudentSubject
import random
import string
import re

# Форма для реєстрації учня 
class RegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control',  'autocomplete': 'new-password'}), 
        label='Пароль'
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}), 
        label='Повторіть пароль'
    )

    class Meta:
        model = Student
        fields = ['email', 'full_name', 'class_id', 'photo']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control','autocomplete': 'off'}),
            'class_id': forms.Select(attrs={'class': 'form-control'}),  
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['class_id'].queryset = Class.objects.all()

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 != password2:
            raise ValidationError("Паролі не співпадають")
        return password2

    def save(self, commit=True):
        student = super().save(commit=False)
        student.password_hash = make_password(self.cleaned_data['password1'])

        if commit:
            student.save()
            self.save_m2m()

            class_subjects = ClassSubject.objects.filter(class_id=student.class_id)
            for cs in class_subjects:
                StudentSubject.objects.get_or_create(student=student, subject=cs.subject)

        return student


class EmailForm(forms.Form):
    email = forms.EmailField(label="Електронна пошта", widget=forms.EmailInput(attrs={'class': 'form-control'}))

class VerificationCodeForm(forms.Form):
    verification_code = forms.CharField(label="Код підтвердження", widget=forms.TextInput(attrs={'class': 'form-control'}))

class NewPasswordForm(forms.Form):
    password1 = forms.CharField(label='Новий пароль', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label='Повторіть пароль', widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password1") != cleaned_data.get("password2"):
            self.add_error("password2", "Паролі не збігаються")


class TeacherRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control','autocomplete': 'new-password'}),
        label='Пароль'
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password' }),
        label='Повторіть пароль'
    )
    is_class_teacher = forms.BooleanField(
        required=False,
        label='Я є класним керівником',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    class_teacher_of = forms.ModelChoiceField(
        queryset=Class.objects.all(),
        required=False,
        label='Клас, у якого ви класний керівник',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
   
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'select2', 'style': 'width: 100%; height: auto;'}),
        label='Предмети, які ви викладаєте'
        
    )

    teaching_classes = forms.ModelMultipleChoiceField(
        queryset=Class.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'select2', 'style': 'width: 100%; height: 100%;'}),
        label='Класи, у яких ви викладаєте',
    )

    class Meta:
        model = Teacher
        fields = ['email', 'full_name', 'is_class_teacher', 'class_teacher_of', 'subjects', 'teaching_classes', 'photo']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control','autocomplete': 'off'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(TeacherRegistrationForm, self).__init__(*args, **kwargs)
        self.fields['class_teacher_of'].queryset = Class.objects.all()
        self.fields['subjects'].queryset = Subject.objects.all()
        self.fields['teaching_classes'].queryset = Class.objects.all()

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 != password2:
            raise ValidationError("Паролі не співпадають")
        return password2

    def clean(self):
        cleaned_data = super().clean()
        is_class_teacher = cleaned_data.get('is_class_teacher')
        class_teacher_of = cleaned_data.get('class_teacher_of')

        if is_class_teacher and not class_teacher_of:
            raise ValidationError("Будь ласка, оберіть клас, у якого ви класний керівник.")

    def save(self, commit=True):
        teacher = super().save(commit=False)
        teacher.password_hash = make_password(self.cleaned_data['password1'])

        if commit:
            teacher.save() 
            teacher.classes.set(self.cleaned_data['teaching_classes'])
            self.save_m2m()

            for class_instance in self.cleaned_data['teaching_classes']:
                for subject in self.cleaned_data['subjects']:
                    ClassSubject.objects.get_or_create(
                        class_id=class_instance,
                        subject=subject,
                        teacher=teacher
        )
            if teacher.is_class_teacher:
                class_instance = self.cleaned_data.get('class_teacher_of')
                if class_instance:
                    class_instance.class_teacher = teacher
                    class_instance.save()
        return teacher
