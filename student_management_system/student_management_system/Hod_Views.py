from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from sms.models import Course, Batch, CustomUser, Student, Staff, Subject, Staff_Notification, Student_Notification, Staff_Leave, Student_Leave, StudentResult
from django.contrib import messages
from django.db.models import Q, Count
#for direct link access validation
from django.http import HttpResponseForbidden, HttpResponseRedirect
from functools import wraps
# from django.urls import reverse


def hod_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.user_type == "1":  # HOD user_type
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("ERROR")
    return _wrapped_view

@login_required(login_url='/')
def HOME(request):
    # print("User Type:", request.user.user_type) 
    student_count=Student.objects.all().count()
    staff_count=Staff.objects.all().count()
    course_count=Course.objects.all().count()
    subject_count=Subject.objects.all().count()
    
    latest_batch_id = Batch.objects.all().order_by('-batch_start').first().id
    print(latest_batch_id)
    previous_batch_id = Batch.objects.all().order_by('-batch_start')[:2][1].id
    print(previous_batch_id)
            
    
    #temp for roll
    courses_with_student_count = Course.objects.annotate(student_count=Count('student'))
    # for course in courses_with_student_count:
    #     print(f"Course: {course.name}, Number of Students: {course.student_count}")

    student_gender_male=Student.objects.filter(gender='Male').count()
    student_gender_female=Student.objects.filter(gender='Female').count()

    context={
        'student_count':student_count,
        'staff_count':staff_count,
        'course_count':course_count,
        'subject_count':subject_count,
        'student_gender_male':student_gender_male,
        'student_gender_female':student_gender_female,
    }
    return render(request, 'Hod/home.html',context)


@login_required(login_url='/')
@hod_required
def ADD_STUDENT(request):
    course = Course.objects.all()
    batches = Batch.objects.all().order_by('-batch_start')[:2]
    
    if request.method=="POST":
        profile_pic = request.FILES.get('profile_pic')
        first_name = request.POST.get('first_name').capitalize()
        last_name = request.POST.get('last_name').capitalize()
        email = request.POST.get('email')
        password = request.POST.get('password')
        username= request.POST.get('username').capitalize()
        address = request.POST.get('address').capitalize()
        gender = request.POST.get('gender')
        course_id=request.POST.get('course_id')#this is grade
        batch_id = request.POST.get('batch_id')
        # print(f'cid={course_id},{Batch.objects.all().order_by('-batch_start')[:2][1]},b_id={batch_id}')
        # print(f'{type(course_id)},{type(Batch.objects.all().order_by('-batch_start')[:2][1])},{type(batch_id)}')
        content={
            'profile_pic' : profile_pic if profile_pic else None,
            'first_name' : first_name,
            'last_name' : last_name,
            'email' : email,
            'password' : password,
            'username' : username,
            'address' : address,
            'gender' : gender,
            'course' : course,
            'batch' : batches,
        }

        #previous and latest batch id needed for validation
        latest_batch_id = Batch.objects.all().order_by('-batch_start')[:2][0].id
        previous_batch_id = Batch.objects.all().order_by('-batch_start')[:2][1].id
        # print(previous_batch_id,latest_batch_id)
            
        # Validate if the email is a Gmail address
        if  not email.endswith('@gmail.com'):
            messages.error(request, 'Email must be a valid Gmail address ending with @gmail.com')
            return render(request,'Hod/add_student.html',content)
        
        if  email == "@gmail.com":
            messages.error(request, 'Email cannot be just @gmail.com, please provide a valid gmail.')
            return render(request,'Hod/add_student.html',content)
        
        if CustomUser.objects.filter(email=email).exists():
            messages.warning(request,'Email already taken')
            return render(request,'Hod/add_student.html',content)
        
        if CustomUser.objects.filter(username=username).exists():
            messages.warning(request,'username already taken')
            return render(request,'Hod/add_student.html',content)

        if gender == "":
            messages.error(request, 'Please select a valid gender')
            return render(request,'Hod/add_student.html',content)
        
        # Validate course_id
        # print(f'course_id= {course_id}, batch_id={batch_id}, previous_batch_id={previous_batch_id}')
        if course_id == "":
            messages.warning(request, 'Please select a valid course')
            return render(request,'Hod/add_student.html',content)
        
        elif int(course_id)==5 and int(batch_id)==previous_batch_id:
            print('its in elif')
            messages.warning(request, f"Grade 11 can only be assigned to latest batch that is {Batch.objects.all().order_by('-batch_start')[:2][0]}")
            return render(request,'Hod/add_student.html',content) 
        
        elif int(course_id)==4 and int(batch_id)==latest_batch_id:
            print('its in elif')
            print(f'lat={Batch.objects.all().order_by('-batch_start')[:2][0]},prev={Batch.objects.all().order_by('-batch_start')[:2][1]}')
            messages.warning(request, f"Grade 12 can only be assigned to previous batch that is {Batch.objects.all().order_by('-batch_start')[:2][1]}")
            return render(request,'Hod/add_student.html',content) 
        
        if batch_id == "":
            messages.error(request, 'Please select a valid course')
            return render(request,'Hod/add_student.html',content)
        
        
        else:
            user=CustomUser(
                first_name=first_name,
                last_name=last_name,
                email=email,
                profile_pic=profile_pic,
                user_type= 3,
                username=username
            )
            user.set_password(password)
            user.save()
            

            course=Course.objects.get(id= course_id)
            batch = Batch.objects.get(id=batch_id)

            #code for generating rollno                   
            main_roll = STUDENT_ROLL(course_id,batch_id)

            student=Student(
                admin=user,
                address=address,
                batch_id = batch,
                course_id=course,
                gender=gender,
                rollno=main_roll
            )
            print(email,password)
            student.save()
            messages.success(request,'Student is sucessfully added.')
            return redirect('add_student')
    context={
        'course' : course,
        'batch' : batches,
    }
    return render(request,'Hod/add_student.html',context)

@login_required(login_url='/')
def VIEW_STUDENT(request):
    student= Student.objects.all()
    context={
        'student': student,
    }
    return render(request,'Hod/view_student.html',context)

@login_required(login_url='/')
@hod_required
def EDIT_STUDENT(request,id):
    print(f'editid= {id}')

    student = Student.objects.filter(id=id)
    StudentId=Student.objects.get(id=id)
    course= Course.objects.all()
    batch = Batch.objects.all()

    context={
        'student': student,
        'course': course,
        'batch' : batch,
        'prev_batch_year_start' : StudentId.batch_id.batch_start,
        'prev_batch_year_end' : StudentId.batch_id.batch_end
    }
    return render(request,'Hod/edit_student.html',context)

@login_required(login_url='/')
@hod_required
def DELETE_STUDENT(request,admin):
    student=CustomUser.objects.get(id = admin)
    student.delete()
    messages.success(request,'Records are Successfully deleted')
    return redirect('view_student')

@login_required(login_url='/')
@hod_required
def UPDATE_STUDENT(request):
    if request.method=="POST":
        student_id=request.POST.get('student_id')
        profile_pic=request.FILES.get('profile_pic')
        first_name = request.POST.get('first_name').capitalize()
        last_name = request.POST.get('last_name').capitalize()
        email = request.POST.get('email')
        password = request.POST.get('password')
        username= request.POST.get('username').capitalize()
        address = request.POST.get('address').capitalize()
        gender = request.POST.get('gender')
        course_id=request.POST.get('course_id')
        batch_id = request.POST.get('batch_id')        
        main_roll = request.POST.get('roll')
        student_table_id = request.POST.get('studentid')

        studentId = Student.objects.get(id= student_table_id)
        customstudent = CustomUser.objects.get(id = student_id)
        context = {
            'student': Student.objects.filter(id = student_table_id),
            'course': Course.objects.all(),
            'batch' : Batch.objects.all(),
            'prev_batch_year_start' : studentId.batch_id.batch_start,
            'prev_batch_year_end' : studentId.batch_id.batch_end
        }

        # From here
        
        #previous and latest batch id needed for validation
        latest_batch_id = Batch.objects.all().order_by('-batch_start')[:2][0].id
        previous_batch_id = Batch.objects.all().order_by('-batch_start')[:2][1].id
        print(previous_batch_id,latest_batch_id)
            
        if int(course_id)==5 and int(batch_id)==previous_batch_id:
            messages.warning(request, f"Grade 11 can only be assigned to latest batch that is {Batch.objects.all().order_by('-batch_start')[:2][0]}")
            return render(request,'Hod/edit_student.html', context)
        
        elif int(course_id)==4 and int(batch_id)==latest_batch_id:
            messages.warning(request, f"Grade 12 can only be assigned to previous batch that is {Batch.objects.all().order_by('-batch_start')[:2][1]}")
            return render(request,'Hod/edit_student.html', context)
        
        # print(f'cid= {course_id}, bid= {batch_id}, sid={studentId.batch_id.id}')
        if studentId.batch_id != batch_id :
            mainroll = STUDENT_ROLL(course_id, batch_id)
        
        if  username != customstudent.username and CustomUser.objects.filter(username=username).exists():
            messages.warning(request,'username already taken')
            return render(request,'Hod/edit_student.html',context)

        if  not email.endswith('@gmail.com'):
            messages.error(request, 'Email must be a valid Gmail address ending with @gmail.com')
            return render(request,'Hod/edit_student.html',context)
        
        if  email == "@gmail.com":
            messages.error(request, 'Email cannot be just @gmail.com, please provide a valid gmail.')
            return render(request,'Hod/edit_student.html',context)
        
        if email != customstudent.email and CustomUser.objects.filter(email=email).exists():
            messages.warning(request,'Email already taken')
            return render(request,'Hod/edit_student.html',context)
        
        #upto here

        user=CustomUser.objects.get(id=student_id)

        user.first_name=first_name
        user.last_name=last_name
        user.email=email
        user.username=username
        # user.first_name=first_name
        if password != None and password!="":
                user.set_password(password)
        if profile_pic != None and profile_pic!="":
                user.profile_pic=profile_pic

        user.save()

        student=Student.objects.get(admin=student_id)
        student.address=address
        student.gender=gender
        student.rollno = mainroll

        course = Course.objects.get(id=course_id)
        student.course_id=course
        batch=Batch.objects.get(id=batch_id)
        student.batch_id=batch
        student.save()
        # print('its here')
        messages.success(request,'Record are sucessfully Updated')
        # print('its here also')
        return redirect('view_student')
    
    return render(request,'Hod/edit_student.html')

@login_required(login_url='/')
@hod_required
def ADD_SUBJECT(request):
    course = Course.objects.all()
    # staff= Staff.objects.all()
    context={
        'course': course,            
        #  'staff': staff,
    }
    if request.method=="POST":
        subject_name=request.POST.get('subject_name')
        course_id=request.POST.get('course_id')
        #  print(staff)
        course=Course.objects.get(id=course_id)
        subject_name = subject_name.strip().lower()
        if Subject.objects.filter(name__iexact=subject_name).exists():
            messages.error(request,'Same Subject already exits.')
            return render(request,'Hod/add_subject.html',context)    

        subject = Subject(
              name = subject_name,
              course = course,
        )
        subject.save()
        messages.success(request,'Subject is Successfully added !')
        return redirect('add_subject')
   
    return render(request,'Hod/add_subject.html',context)

@login_required(login_url='/')
@hod_required
def ADD_STAFF(request):
    subjects = Subject.objects.all()
    context= {
        'subjects' : subjects
    }
    if request.method =="POST":
        profile_pic = request.FILES.get('profile_pic')
        first_name = request.POST.get('first_name').capitalize()
        last_name = request.POST.get('last_name').capitalize()
        email = request.POST.get('email')
        password = request.POST.get('password')
        username= request.POST.get('username').capitalize()
        address = request.POST.get('address').capitalize()
        gender = request.POST.get('gender')
        subjects = request.POST.getlist('assigning_subjects')
        subjects = list(set(subjects))

        # print(profile_pic,first_name,last_name,username,password,address,gender,email)

        if CustomUser.objects.filter(email=email).exists():
            messages.warning(request,'Email already exist')
            return redirect('add_staff')
        if CustomUser.objects.filter(username=username).exists():
            messages.warning(request,'username already exist')
            return redirect('add_staff')
        else:
            user=CustomUser(first_name=first_name, last_name=last_name, username=username, email=email, profile_pic=profile_pic, user_type=2)
            user.set_password(password)
            user.save()

            staff = Staff(
                admin = user,
                address = address,
                gender= gender,
            )
            staff.save()
            if subjects:
                staff.subjects.set(subjects)
            messages.success(request,'Staff is successfully added ! ')
            return redirect('add_staff')
        
    return render(request,'Hod/add_staff.html',context)

@login_required(login_url='/')
@hod_required
def EDIT_SUBJECT(request,id):
     subject= Subject.objects.get(id= id)
     course=Course.objects.all()
     subject_course = subject.course.id
     context={
         'subject':subject,
         'course':course,
         'subject_course': subject_course
     }
     return render(request,'Hod/edit_subject.html',context)

@login_required(login_url='/')
@hod_required
def UPDATE_SUBJECT(request):
    
    if request.method == "POST":
        subject_id = request.POST.get('subject_id')
        subject_name = request.POST.get('subject_name')
        course_id = request.POST.get('course_id')

        try:
            # Check if a valid course is selected
            if course_id == "Select Grade":
                raise ValueError("Please select a valid course")
            
            # Retrieve the corresponding Course object based on the provided course ID
            course = Course.objects.get(id=course_id)

            # Retrieve the corresponding Subject object based on the provided subject ID
            subject = Subject.objects.get(id=subject_id)
            subject.name = subject_name
            subject.course = course
            subject.save()

            # Display a success message and redirect to the view for viewing subjects
            messages.success(request, 'Subject is successfully updated')
            return redirect('view_subject')

        except ValueError as ve:
            # If a ValueError occurs (invalid course selection), display an error message to the user
            messages.error(request,"Please select valid course")
            return redirect('edit_subject', id=subject_id)

@login_required(login_url='/')
def VIEW_SUBJECT(request):
     subject= Subject.objects.all()
     context={
          'subject': subject,

     }
     return render(request,'Hod/view_subject.html',context)

@login_required(login_url='/')
@hod_required
def VIEW_STAFF(request):
    staff=Staff.objects.all()
    context={
        'staff':staff,
    }
    return render(request,'Hod/view_staff.html',context)

@login_required(login_url='/')
@hod_required
def EDIT_STAFF(request,id):
    # staff = Staff.objects.get(admin_id=id)
    staff=Staff.objects.get(id=id)
    assigned_subjects = staff.subjects.all()
    remaining_subjects = Subject.objects.exclude(id__in=assigned_subjects.values_list('id', flat=True)) 
    context={
        'staff':staff,
        'assigned_subjects': assigned_subjects,
        'remaining_subjects': remaining_subjects
    }
    return render(request,'Hod/edit_staff.html',context)

@login_required(login_url='/')
@hod_required
def UPDATE_STAFF(request):
    if request.method=="POST":
        staff_id =  request.POST.get('staff_id')
        profile_pic = request.FILES.get('profile_pic')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        username= request.POST.get('username')
        address = request.POST.get('address')
        gender = request.POST.get('gender')
        subjects = request.POST.getlist('subjects')
        remaining_sub = request.POST.getlist('remaining_subjects')

        # Combine subjects and remaining_sub
        all_subjects = list(set(subjects + remaining_sub))

        user = CustomUser.objects.get(id=staff_id)
        user.username=username
        user.first_name=first_name
        user.last_name=last_name
        user.email=email
        if password != None and password!="":
                user.set_password(password)
        if profile_pic != None and profile_pic!="":
                user.profile_pic=profile_pic

        user.save()

        staff = Staff.objects.get(admin=staff_id)
        staff.gender=gender
        staff.address=address
        if all_subjects:  # Update subjects only if provided
            staff.subjects.set(all_subjects)
        staff.save()
        messages.success(request,'Staff is successfully updated')
        return redirect('view_staff')

    return render(request,'Hod/edit_staff.html')

@login_required(login_url='/')
@hod_required
def DELETE_STAFF(request,admin):
     staff=CustomUser.objects.get(id=admin)
     staff.delete()
     messages.success(request,'Staff is deleted sucessfully')
     return redirect('view_staff')

@login_required(login_url='/')
@hod_required
def STAFF_SEND_NOTIFICATION(request):
    return render(request,'Hod/staff_notification.html')

@login_required(login_url='/')
@hod_required     
def DELETE_SUBJECT(request,id):
     subject=Subject.objects.filter(id=id)
     subject.delete()
     messages.success(request,'Subject is deleted')
     return redirect('view_subject')

@login_required(login_url='/')
@hod_required
def ADD_BATCH(request):
    if request.method == "POST":
        batch_start = request.POST.get('batch_year_start')
        batch_end = request.POST.get('batch_year_end')

        batch = Batch(
             batch_start = batch_start,
             batch_end = batch_end
        )
        batch.save()
        messages.success(request, 'Batch is Successfully Created')
        return redirect('add_batch')
    return render(request,'Hod/add_batch.html')

@login_required(login_url='/')
@hod_required
def VIEW_BATCH(request):
    batches = Batch.objects.all()

    context = {
        'batch' : batches,
    }
    return render(request,'Hod/view_batch.html',context)

@login_required(login_url='/')
@hod_required
def EDIT_BATCH(request,id):
    batch = Batch.objects.filter(id =id)

    context = {
        'batch' : batch,
    }
    return render(request,'Hod/edit_batch.html',context)

@login_required(login_url='/')
@hod_required
def UPDATE_BATCH(request):
    if request.method == "POST":
        batch_id = request.POST.get('batch_id')
        batch_start = request.POST.get('batch_start')
        batch_end = request.POST.get('batch_end')
        
        # Check if another batch with the same start and end year exists
        if Batch.objects.filter(
            Q(batch_start=batch_start) & 
            Q(batch_end=batch_end) & 
            ~Q(id=batch_id)  # Exclude the current batch being edited
        ).exists():
            messages.error(request, 'A batch with the same start and end year already exists!')
            return redirect('edit_batch', id=batch_id)

        # Update session information
        try:
            batch = Batch.objects.get(id=batch_id)
            batch.batch_start = batch_start
            batch.batch_end = batch_end
            batch.save()
            messages.success(request, 'Batch is successfully updated!')
        except Batch.DoesNotExist:
            messages.error(request, 'Batch not found!')

    return redirect('view_batch')

@login_required(login_url='/')
@hod_required
def DELETE_BATCH(request, id):
    # batch = Batch.objects.get(id = id)
    # batch.delete()
    # messages.success(request,'Batch is successfully  Deleted !')
    batch = get_object_or_404(Batch, id=id)
    
    # Check if any student is associated with this batch
    if Student.objects.filter(batch_id = batch.id).exists():
        messages.error(request, "This batch cannot be deleted because it contains students!")
    else:
        batch.delete()
        messages.success(request, "Batch is successfully deleted!")

    return redirect('view_batch')

@login_required(login_url='/')
@hod_required
def HOD_VIEW_PROFILE_STAFF(request,id):
    user = Staff.objects.get(id=id)
    assigned_subjects = user.subjects.all()
    user_id = user.admin
    print(f"user_id={id}, mainid={user_id.id}")
    context={
        "fname" : user_id.first_name,
        "lname" : user_id.last_name,
        "profile_picture" : user_id.profile_pic.url if user.admin.profile_pic else None,
        "s_grade" : user_id,
        "s_gender" : user.gender,
        "s_address" : user.address,
        "s_email" : user_id.email,
        "s_username" : user_id.username,
        "assigned_subjects": assigned_subjects,
        "staff_id" : id,
        "staff_main_id": user_id.id
    }
    return render(request,'Hod/hod_view_profile_staff.html',context)

@login_required(login_url='/')
# @hod_required
def HOD_VIEW_PROFILE_STUDENT(request,id):
    user = Student.objects.get(id=id)
    user_id = user.admin
    context={
        "fname" : user_id.first_name,
        "lname" : user_id.last_name,
        "profile_picture" : user_id.profile_pic.url if user.admin.profile_pic else None,
        "s_grade" : user_id,
        "s_gender" : user.gender,
        "s_address" : user.address,
        "s_email" : user_id.email,
        "s_username" : user_id.username,
        "grade" : user.course_id,
        "rollno" : user.rollno,
        "stud_id": id,
        "stud_main_id": user_id.id,
    }
    return render(request,'Hod/hod_view_profile_student.html',context)

@login_required(login_url='/')
@hod_required
def STAFF_SEND_NOTIFICATION(request):
    staff = Staff.objects.all()
    see_notification = Staff_Notification.objects.all().order_by('-id')[0:20]  #0:5 to show only 5 message
    context={
        'staff': staff,
        'see_notification': see_notification,
    }
    return render(request,'Hod/staff_notification.html',context)

@login_required(login_url='/')
@hod_required
def SAVE_STAFF_NOTIFICATION(request):
    if request.method == "POST":
        staff_id = request.POST.get('staff_id')
        message = request.POST.get('message')

        staff = Staff.objects.get(admin = staff_id)
        notification = Staff_Notification(
            staff_id = staff,
            message = message,
        )
        notification.save()
        messages.success(request, 'Notification sent successfully')
    return redirect('staff_send_notification')

@login_required(login_url='/')
@hod_required
def STUDENT_SEND_NOTIFICATION(request):
    student = Student.objects.all()
    # see_notification = Student_Notification.objects.all()  #0:5 to show only 5 message
    see_notification = Student_Notification.objects.all().order_by('-id')[0:20]  #0:5 to show only 5 message
    context={
        'student': student,
        'see_notification': see_notification,
    }
    return render(request,'Hod/student_notification.html',context)

@login_required(login_url='/')
@hod_required
def SAVE_STUDENT_NOTIFICATION(request):
    if request.method == "POST":
        student_id = request.POST.get('student_id')
        message = request.POST.get('message')
        student = Student.objects.get(admin = student_id)
        stud_notification = Student_Notification(
            student_id = student,
            message = message,
        )
        stud_notification.save()
        messages.success(request, 'Notification sent successfully')
    return redirect('student_send_notification')

def GENERATE_ROLLNO(start_roll:str , end_roll:int )->str:
    # print(f'start_roll={start_roll},end_roll={end_roll}')
    padded_roll = str(end_roll).zfill(3)  #if roll=2 then padded_roll=002
    main_roll = str(start_roll) + padded_roll 
    while Student.objects.filter(rollno=main_roll).exists():
        # If the main_roll exists, increment the roll number by 1 and update the main_roll
        end_roll += 1
        padded_roll = str(end_roll).zfill(3)  # Re-pad the roll to 3 digits
        main_roll = str(start_roll) + padded_roll
    return main_roll

def STUDENT_ROLL(s_id: int, b_id: int) -> str:
    """
        s_id: course_id,
        b_id: batch_id,
        This generates rollno and returns it as a string
    """
    student_count = Student.objects.filter(course_id=s_id).count()
    student_batch = Batch.objects.get(id=b_id)
    starting_roll = student_batch.batch_start
    main_roll = GENERATE_ROLLNO(starting_roll, student_count)
    return main_roll

@login_required(login_url='/')
@hod_required
def STAFF_LEAVE_VIEW(request):
    staff_leave = Staff_Leave.objects.all()
    context={
        'staff_leave' : staff_leave,
    }
    return render(request, 'Hod/staff_leave.html',context)

@login_required(login_url='/')
@hod_required
def STAFF_APPROVE_LEAVE(request, id):
    leave = Staff_Leave.objects.get(id= id)
    leave.status = 1 
    leave.save()
    return redirect('staff_leave_view')

@login_required(login_url='/')
@hod_required
def STAFF_DISAPPROVE_LEAVE(request, id):
    leave = Staff_Leave.objects.get(id= id)
    leave.status = 2
    leave.save()
    return redirect('staff_leave_view')

@login_required(login_url='/')
@hod_required
def STUDENT_LEAVE_VIEW(request):
    student_leave = Student_Leave.objects.all()
    print(f'stude= {student_leave}')
    context={
        'student_leave' : student_leave,
    }
    return render(request, 'Hod/student_leave.html',context)

@login_required(login_url='/')
@hod_required
def STUDENT_APPROVE_LEAVE(request, id):
    leave = Student_Leave.objects.get(id= id)
    leave.status = 1 
    leave.save()
    return redirect('student_leave_view')

@login_required(login_url='/')
@hod_required
def STUDENT_DISAPPROVE_LEAVE(request, id):
    leave = Student_Leave.objects.get(id= id)
    leave.status = 2
    leave.save()
    return redirect('student_leave_view')

@login_required(login_url='/')
@hod_required
def HOD_ADD_RESULT(request):
    courses = Course.objects.all()
    # batches = Batch.objects.all()
    batches = Batch.objects.all().order_by('-batch_start')[:2]
    action = request.GET.get('action')

    get_subject = None
    students = None
    
    #previous and latest batch id needed for validation
    latest_batch_id = Batch.objects.all().order_by('-batch_start')[:2][0].id
    previous_batch_id = Batch.objects.all().order_by('-batch_start')[:2][1].id    
    print(f'lbid={latest_batch_id}')

    if action is not None:
        if request.method == "POST":
            course_id = request.POST.get('course_id')
            batch_id = request.POST.get('batch_year_id')
            students  = Student.objects.filter(batch_id = batch_id)

            get_subject = Subject.objects.filter(course_id = course_id)
            if int(course_id)==5 and int(batch_id)==previous_batch_id:
                print('its in elif')
                messages.warning(request, f"Grade 11 can only falls to latest batch that is {Batch.objects.all().order_by('-batch_start')[:2][0]}")
                return redirect('hod_add_result')
            
            elif int(course_id)==4 and int(batch_id)==latest_batch_id:
                print('its in elif')
                print(f'lat={Batch.objects.all().order_by('-batch_start')[:2][0]},prev={Batch.objects.all().order_by('-batch_start')[:2][1]}')
                messages.warning(request, f"Grade 12 can only falls to previous batch that is {Batch.objects.all().order_by('-batch_start')[:2][1]}")
                return redirect('hod_add_result')

    

    context = {
        'courses' : courses,
        'batches' : batches, 
        'action' : action,
        'get_subject' : get_subject,
        'students' : students,
    }
    return render(request, 'Hod/add_result.html',context )

@login_required(login_url='/')
@hod_required
def HOD_SAVE_RESULT(request):
    subject_id = request.POST.get('subject_id')
    student_id = request.POST.get('student_id')
    internal_mark = request.POST.get('internal_mark')
    exam_mark = request.POST.get('exam_mark')

    if int(exam_mark)<0 or int(exam_mark)>80:
        messages.error(request,'Please enter a valid exam mark [0 to 80]')
        return redirect ('hod_add_result')
    
    if int(internal_mark)<0 or int(internal_mark)>25:
        messages.error(request,'Please enter a valid internal mark [0 to 25]')
        return redirect ('hod_add_result')
    

    get_student = Student.objects.get(admin = student_id )
    get_subject = Subject.objects.get(id = subject_id )

    check_exists = StudentResult.objects.filter(subject_id = get_subject, student_id= get_student).exists()
    if check_exists:
        result = StudentResult.objects.get(subject_id = get_subject, student_id = get_student)
        result.internal_mark = internal_mark
        result.exam_mark = exam_mark
        result.save()
        messages.success(request,'Result is Successfully Updated')
        return redirect ('hod_add_result')

    else:
        result = StudentResult(
            student_id = get_student,
            subject_id = get_subject,
            exam_mark = exam_mark,
            internal_mark = internal_mark
        )
        result.save()
        messages.success(request,'Result is Successfully Added')
        return redirect ('hod_add_result')

    return None

@login_required(login_url='/')
@hod_required
def HOD_VIEW_RESULT(request):
    batches = Batch.objects.all()
    action = request.GET.get('action')

    # get_subject = None
    students =None
    course_id = None
    print(f'a={action}')
    if action != None:
        if request.method == "POST":
            batch_id = request.POST.get('batch_id')
            students  = Student.objects.filter(batch_id = batch_id)

    context={
        'batches': batches,
        'students' : students,
        # 'get_subject' :get_subject,
        'action' : action,
    }
    print(course_id)
    return render(request, 'Hod/hod_view_result.html',context)

@login_required(login_url='/')
@hod_required
def HOD_VIEW_STUDENT_RESULT(request):
    student_id = request.POST.get('student_id')
    student = Student.objects.get(id=student_id)
    course_id = student.course_id.id
    subjects = Subject.objects.filter(course_id=course_id)
    
    results = []
    for subject in subjects:
        try:
            result = StudentResult.objects.get(student_id=student, subject_id=subject)
            results.append({
                'subject_id': subject,
                'internal_mark': result.internal_mark,
                'exam_mark': result.exam_mark,
            })
        except StudentResult.DoesNotExist:
            results.append({
                'subject_id': subject,
                'internal_mark': '-',
                'exam_mark': '-',
            })
    # print(results)
    context = {
        'results': results,
        'student': student,
    }
    return render(request, 'Hod/view_student_result.html', context)

@login_required(login_url='/')
@hod_required
def SEND_NOTIFICATION_TO_ALL_STUDENTS(request):
    if request.method == "POST":
        message = request.POST.get('message')
        students = Student.objects.all()
        for student in students:
            stud_notification = Student_Notification(
                student_id=student,
                message=message,
            )
            stud_notification.save()
        messages.success(request, 'Notification sent to all students successfully.')
    return redirect('student_send_notification')

@login_required(login_url='/')
@hod_required
def SEND_NOTIFICATION_TO_ALL_STAFFS(request):
    if request.method == "POST":
        message = request.POST.get('message')
        staffs = Staff.objects.all()
        for staff in staffs:
            staff_notification = Staff_Notification(
                staff_id=staff,
                message=message,
            )
            staff_notification.save()
        messages.success(request, 'Notification sent to all staffs successfully.')
    return redirect('staff_send_notification')
