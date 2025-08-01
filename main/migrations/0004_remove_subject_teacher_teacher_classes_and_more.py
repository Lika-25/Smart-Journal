# Generated by Django 5.0.1 on 2025-05-08 11:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_alter_class_name_alter_teacher_full_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='subject',
            name='teacher',
        ),
        migrations.AddField(
            model_name='teacher',
            name='classes',
            field=models.ManyToManyField(blank=True, related_name='teaching_teachers', to='main.class'),
        ),
        migrations.AddField(
            model_name='teacher',
            name='subjects',
            field=models.ManyToManyField(blank=True, to='main.subject'),
        ),
        migrations.AlterField(
            model_name='class',
            name='name',
            field=models.CharField(choices=[('1А', '1А'), ('1Б', '1Б'), ('1В', '1В'), ('1Г', '1Г'), ('2А', '2А'), ('2Б', '2Б'), ('2В', '2В'), ('2Г', '2Г'), ('3А', '3А'), ('3Б', '3Б'), ('3В', '3В'), ('3Г', '3Г'), ('4А', '4А'), ('4Б', '4Б'), ('4В', '4В'), ('4Г', '4Г'), ('5А', '5А'), ('5Б', '5Б'), ('5В', '5В'), ('11А', '11А'), ('11Б', '11Б'), ('11В', '11В'), ('11Г', '11Г')], max_length=50),
        ),
        migrations.AlterField(
            model_name='subject',
            name='name',
            field=models.CharField(max_length=255),
        ),
    ]
