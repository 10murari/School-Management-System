# Generated by Django 5.1 on 2025-01-08 15:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sms', '0024_batch_remove_student_session_year_id_staff_subjects_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='student',
            name='batch_id',
        ),
    ]
