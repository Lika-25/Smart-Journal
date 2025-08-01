
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    path('', views.index, name='main'),  # выбор Вход/Регистрация
    path('logout/', views.logout_view, name='logout'),
    path('chose-role/', views.chose_role, name='chose_role'),  # выбор роли
    path('register/student/', views.register_student, name='register_student'),
    path('register/teacher/', views.register_teacher, name='register_teacher'),
    path('login/', views.login_view, name='login'),
    path('set_new_password/', views.set_new_password, name='set_new_password'),


    # для учителя
    path('teacher/profile/', views.teacher_profile, name='teacher_profile'),
    path('teacher/profile/update/', views.update_teacher_profile, name='update_teacher_profile'),
    path('teacher/class/', views.teacher_class, name='teacher_class'),
    path('teacher/grades/', views.teacher_grades, name='teacher_grades'),
    
    # для ученика
    path('student/profile/', views.student_profile, name='student_profile'),
    path('student/profile/update/', views.update_student_profile, name='update_student_profile'),
    path('student/grades/', views.student_grades, name='student_grades'),
    path('student/class/', views.student_class, name='student_class'),
    path('student/notifications/', views.student_notifications, name='student_notifications'),

    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)