from django.shortcuts import render,redirect
from sms.models import *
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from functools import wraps
from django.http import HttpResponseForbidden

def staff_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.user_type == "2":  # staff user_type
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("ERROR")
    return _wrapped_view

@login_required(login_url='/')
def HOME(request):
    return redirect('hod_home')

@login_required(login_url='/')
@staff_required
def STAFF_NEW_PASSWORD(request):
    if request.method == "POST":
        old_password = request.POST.get('staff_old_password')
        new_password = request.POST.get('staff_new_password')
        confirm_password = request.POST.get('staff_confirm_password')

        user = request.user  # You can directly use the logged-in user

        # Check if the old password is correct
        if not user.check_password(old_password):
            messages.error(request, "The old password you entered is incorrect.")
            return render(request,'Staff/staff_new_password.html')

        # Check if the new password matches the confirmation password
        if new_password != confirm_password:
            messages.error(request, "New password and confirm password do not match.")
            return render(request,'Staff/staff_new_password.html')

        # Check if the new password is the same as the old password
        if new_password == old_password:
            messages.error(request, "Your new password cannot be the same as your current password. Please choose a different password.")
            return render(request,'Staff/staff_new_password.html')

        # Set the new password
        user.set_password(new_password)
        user.save()

        messages.success(request, "Your password has been successfully updated.")

        # Add a message that the user will be logged out after a countdown
        # Redirect to the login page after success and countdown
        return render(request, 'Staff/staff_logout_countdown.html')

    return render(request, 'Staff/staff_new_password.html')


@login_required(login_url='/')
@staff_required
def STAFF_VIEW_SUBJECTS(request, id):
    staff = Staff.objects.get(admin_id=id)
    assigned_subjects = staff.subjects.all()
    remaining_subjects = Subject.objects.exclude(id__in=assigned_subjects.values_list('id', flat=True))
    
    context = {
        'assigned_subjects': assigned_subjects,
        'remaining_subjects': remaining_subjects,
    }
    return render(request, 'Staff/staff_view_subjects.html', context)


@login_required(login_url='/')
@staff_required
def STAFF_VIEW_STUDENTS(request,id):
    staff = Staff.objects.get(admin_id=id)
    
    # Get all subjects assigned to this staff member
    subjects = Subject.objects.filter(id__in=staff.subjects.values('id'))  # Assuming `staff.subjects` gives related subjects
    
    # Get all students affiliated with the courses of these subjects
    students = Student.objects.filter(course_id__in=subjects.values('course_id'))
    
    context = {
        'affiliated_students': students,
    }
    return render(request, 'Staff/staff_view_students.html', context)


@login_required(login_url='/')
@staff_required
def NOTIFICATIONS(request):
    staff = Staff.objects.filter(admin = request.user.id)
    for i in staff:
        staff_id = i.id
    notification = Staff_Notification.objects.filter(staff_id = staff_id)
    context = {
        'notification': notification,
    }
    return render(request,'Staff/notifications.html',context)


@login_required(login_url='/')
@staff_required
def STAFF_NOTIFICATION_MARK(request,status):
    notification = Staff_Notification.objects.get(id= status)
    notification.status = 1
    notification.save()
    return redirect('notifications')


@login_required(login_url='/')
@staff_required
def STAFF_APPLY_LEAVE(request):
    staff = Staff.objects.filter(admin = request.user.id)
    for i in staff:
        staff_id = i.id 
    staff_leave_history = Staff_Leave.objects.filter(staff_id = staff_id)
    context={
        'staff_leave_history' : staff_leave_history,
    }
    return render(request, 'Staff/apply_leave.html', context)


@login_required(login_url='/')
@staff_required
def STAFF_APPLY_LEAVE_SAVE(request):
    if request.method=="POST":
        leave_date = request.POST.get('leave_date')
        leave_message = request.POST.get('leave_message')
        
        staff = Staff.objects.get(admin = request.user.id)

        leave = Staff_Leave(
            staff_id = staff,
            date = leave_date,
            message = leave_message
        )
        leave.save()
        messages.success(request, 'Leave message successfully sent')
    return redirect('staff_apply_leave')
