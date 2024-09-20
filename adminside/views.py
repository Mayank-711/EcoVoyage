from django.shortcuts import render

# Create your views here.
def adminlogin(request):
    return render(request,'adminapp/alogin.html')

def view_feedback(request):
    return render(request,'adminapp/feedback.html')

def add_store(request):
    return render(request,'adminapp/addstore.html')