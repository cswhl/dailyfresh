from django.shortcuts import render

# Create your views here.
def index(request):
    '''网站首页'''

    return render(request, 'index.html')
