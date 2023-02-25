from datetime import datetime, timedelta
from django.utils.timezone import now
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import HttpResponse, redirect, render
from django.contrib.auth.models import User
from .models import Concert, Performance
from django.contrib.auth.decorators import login_required


# Create your views here.
def index(request):
    # Get concerts IN THE FUTURE
    concerts = Concert.objects.filter(dateandtime__gte = now()).order_by('dateandtime')
    print(request.user.groups.filter(name='event-manager').exists())
    print(concerts)
    print(True if concerts else False)
    # Get list of concerts that user has signed up for
    signedupconcerts = []
    return render(request, 'signup/index.html', {
        "concerts": concerts,
        "ismanager": request.user.groups.filter(name='event-manager').exists(),
        "concertsexist": True if concerts else False,
    })


def listconcert(request):
    # list concerts in 2 sections
    upcoming = Concert.objects.filter(dateandtime__gte = now()).order_by('dateandtime')
    previous = Concert.objects.filter(dateandtime__lt = now()).order_by('dateandtime')
    return render(request, "signup/listconcert.html" ,{
        'upcoming': upcoming,
        'previous': previous,
        'ismanager': request.user.groups.filter(name='event-manager').exists(),
        "concertsexist": True if upcoming else False
    })


@login_required()
def createconcert(request):
    if request.method == "GET":
        if not request.user.groups.filter(name='event-manager').exists():
            raise PermissionDenied() 
        return render(request=request, template_name="signup/createconcert.html")
    elif request.method == "POST":
        if not request.user.groups.filter(name='event-manager').exists():
            raise PermissionDenied() 
        # print(request.user.groups.filter('event-manager').exists())
        #if not request.user.groups.filter('event-manager').exists():
        #    return HttpResponse("Oh no! You aren't an event coordinator, so you cannot create events!", status=400)
        eventmanager = request.user
        dateandtime = request.POST.get('datetime')
        location = request.POST.get('location')
        maxduration = request.POST.get('maxtime')
        description = request.POST.get('description')
        piano = True if request.POST.get('piano') else False
        print(dateandtime)
        newconcert = Concert(location = location, dateandtime = dateandtime, maxtime = maxduration, piano = piano, description = description)
        newconcert.save()
        newconcert.manager.set([eventmanager])
        newconcert.save()
        messages.success(request, "Created new concert!")
        return redirect("concertpage", newconcert.id)

@login_required
def newperformance(request, concert_id):
    concert = Concert.objects.filter(id=concert_id)
    if not concert:
        return render(request, "404.html")
    concert: Concert = concert[0]
    # check if concert is locked
    iseventmanager = request.user.groups.filter(name='event-manager').exists()
    if concert.locked and not iseventmanager:
        return HttpResponse("Error: This event has been locked. New performances are disabled.")
    totaltimes = 0
    for performance in concert.performance_set.all():
        totaltimes += performance.duration
    # Check concert date
    if concert.dateandtime < now():
        concert.locked = True
        concert.save()
    
    if totaltimes >= concert.maxtime and not iseventmanager:
        concert.locked = True
        concert.save()
        return HttpResponse("Error: This event has been locked. New performances are disabled.")

    
    if request.method == "GET":
        # get list of users
        performers = User.objects.all().order_by('last_name').values()
        return render(request, "signup/newperformance.html", {
            "concert": concert,
            "performers": performers,
            "iseventmanager": iseventmanager
        })
    elif request.method == "POST":
        print(request.POST)
        performers_raw = request.POST.getlist("performers")
        print(type(performers_raw))
        print("Performers " + str(performers_raw))
        performers = []
        for performer in performers_raw:
            print(performer)
            performers.append(User.objects.get(id=performer))
        piece = request.POST.get('piece')
        composer = request.POST.get('composer')
        arranger = request.POST.get('arranger')
        duration = request.POST.get('duration')
        comment = request.POST.get('comment')
        if not duration or not composer or not piece or not performers:
            messages.error(request, "Your request was automatically rejected. Please check the accuracy of all fields and resubmit.")
            return redirect("concertpage", concert_id=concert_id)
        if int(duration) + totaltimes >= concert.maxtime + 10 and not iseventmanager:
            # deny
            messages.warning(request, "Your performance was too long and so it was rejected automatically!")
            return redirect("signup-index")
        if iseventmanager and int(duration) + totaltimes >= concert.maxtime:
            concert.locked = True
            concert.save()
        performance = Performance(concert = concert, piece=piece, composer=composer, arranger=arranger, duration=int(duration), comment=comment)
        performance.save()
        performance.performer.set(performers)
        messages.success(request, "You successfully requested a performance!")
        return redirect("concertpage", concert_id=concert_id)


@login_required()
def concertpage(request, concert_id):
    try:
        concert = Concert.objects.get(id=concert_id)
    except Exception:
        return render(request, "404.html")
    if concert.dateandtime < now():
        concert.locked = True
        concert.save()
    useriseventmanager = False
    if request.user.groups.filter(name="event-manager").exists():
        useriseventmanager = True
    return render(request, 'signup/concertpage.html', {
        "concert": concert,
        "useriseventmanager": useriseventmanager
    })


@login_required()
def editconcert(request, concert_id):
    try:
        concert = Concert.objects.get(id=concert_id)
    except Exception:
        return render(request, "404.html")
    if not request.user.groups.filter(name='event-manager').exists():
        raise PermissionDenied() 
    if request.method == "GET":
        return render(request, "signup/createconcert.html", {
            "edit": True,
            "concert": concert
        })
    else:
        dateandtime = request.POST.get('datetime')
        location = request.POST.get('location')
        maxduration = request.POST.get('maxtime')
        description = request.POST.get('description')
        piano = True if request.POST.get('piano') else False
        if not dateandtime or not location or not maxduration:
            messages.error(request, "Please fill out all required fields.")
            return redirect("editconcert", concert_id=concert_id)
        concert.dateandtime = dateandtime
        concert.location = location
        concert.maxtime = int(maxduration)
        concert.description = description
        concert.piano = piano
        concert.save()
        totaltimes = 0
        for performance in concert.performance_set.all():
            totaltimes += performance.duration
        if totaltimes < int(maxduration) or concert.dateandtime < now():
            concert.locked = False
            concert.save()
        return redirect("concertpage", concert_id = concert_id)



@login_required()
def deleteconcert(request, concert_id):
    try:
        concert = Concert.objects.get(id=concert_id)
    except Exception:
        return render(request, "404.html")
    if not request.user.groups.filter(name='event-manager').exists():
        raise PermissionDenied() 
    concert.delete()
    messages.success(request, "Concert deleted successfully!")
    return redirect("signup-index")


@login_required()
def lockconcert(request, concert_id):
    try:
        concert = Concert.objects.get(id=concert_id)
    except Exception:
        return render(request, "404.html")
    if not request.user.groups.filter(name='event-manager').exists():
        raise PermissionDenied() 
    if not concert.locked:
        concert.locked = True
        messages.success(request, "Concert locked successfully!")
    else:
        concert.locked = False
        messages.success(request, "Concert unlocked successfully!")
    concert.save()
    
    return redirect("concertpage", concert_id=concert.id)


@login_required()
def myconcerts(request):
    # find user's concert
    allconcerts = Concert.objects.all()
    userconcerts = []
    for concert in allconcerts:
        performances = concert.performance_set.filter(performer=request.user)
        if performances:
            userconcerts.append(concert)
    return render(request, "signup/listconcert.html", {
        "myconcert": True,
        "concerts": userconcerts
    })


def concertjson(request):
    if request.user:
        loggedin = True
    else:
        loggedin = False
    # get start and end dates
    print(type(request.GET.get("start")))
    start = request.GET.get("start")
    end = request.GET.get("end")
    if start and end:
        start = datetime.fromisoformat(start)
        end = datetime.fromisoformat(end)
        concerts_temp = Concert.objects.filter(dateandtime__gt = start, dateandtime__lt = end)
    else:
        start = None
        end = None
        concerts_temp = Concert.objects.all()
    # get concerts
    concerts = []
    for concert in concerts_temp:
        end = concert.dateandtime + timedelta(minutes=concert.maxtime)
        print(end)
        concerts.append({"concert": concert, "end": end})
    return render(request, "signup/concerts.json", {
        "concerts": concerts,
    }, content_type="application/json")

def calendar(request):
    return render(request, "signup/calendar.html")


@login_required()
def editperformance(request, concert_id, performance_id):
    try:
        concert = Concert.objects.get(id=concert_id)
        performance = Performance.objects.get(id=performance_id)
        print(performance_id)
        print(performance.id)
    except Exception:
        return render(request, "404.html")
    iseventmanager = request.user.groups.filter(name='event-manager').exists()
    if not(request.user.groups.filter(name='event-manager').exists() or performance.performer.filter(id=request.user.id).exists()):
        raise PermissionDenied() 
    totaltimes = 0
    for performancex in concert.performance_set.all():
        totaltimes += performancex.duration
    if request.method == "GET":
        performers = User.objects.all().order_by('last_name').values()
        performanceperformers = performance.performer.all().values_list('id', flat=True)
        print(performance.performer.all())
        return render(request, "signup/newperformance.html", {
            "edit": True,
            "concert": concert,
            "performance": performance,
            "performers": performers,
            "performanceperformers": performanceperformers,
            "isedit": True
        })
    else:
        performers_raw = request.POST.getlist("performers")
        performers = []
        for performer in performers_raw:
            print(performer)
            performers.append(User.objects.get(id=performer))
        piece = request.POST.get('piece')
        composer = request.POST.get('composer')
        arranger = request.POST.get('arranger')
        duration = request.POST.get('duration')
        comment = request.POST.get('comment')
        if not duration or not composer or not piece or not performers:
            messages.error(request, "Please fill out required fields.")
            return redirect("concertpage", concert_id=concert_id)
        if int(duration) + totaltimes >= concert.maxtime + 10 and not iseventmanager:
            # deny
            messages.warning(request, "Your revised time was too long!")
            duration = performance.duration
        performance.concert = concert
        performance.piece = piece
        performance.composer = composer
        performance.arranger = arranger
        performance.duration = int(duration)
        performance.comment = comment
        performance.performer.set(performers)
        performance.save()
        if iseventmanager and int(duration) + totaltimes >= concert.maxtime:
            concert.locked = True
            concert.save()
        messages.success(request, "You successfully edited a performance!")
        return redirect("concertpage", concert_id=concert_id)

def deleteperformance(request, concert_id, performance_id):
    try:
        concert = Concert.objects.get(id=concert_id)
        performance = Performance.objects.get(id=performance_id)
    except Exception:
        return render(request, "404.html")
    iseventmanager = request.user.groups.filter(name='event-manager').exists()
    if not(request.user.groups.filter(name='event-manager').exists() or performance.performer.filter(id=request.user.id).exists()):
        raise PermissionDenied() 
    performance.delete()
    messages.success(request, "Performance deleted successfully!")
    return redirect("concertpage", concert_id=concert.id)