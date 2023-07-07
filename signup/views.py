from __future__ import annotations

from datetime import datetime, timedelta
import pytz

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.http import HttpResponse
#from django.http import (HttpResponsePermanentRedirect,
#                         HttpResponseRedirect)
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import Concert, Performance


# Create your views here.
def index(request):
    """
    The home page: display a list of concerts + signup links for them.
    """
    # Get concerts IN THE FUTURE
    try:
        if request.session["USER_TIMEZONE"]:
            timezone.activate(pytz.timezone(request.session["USER_TIMEZONE"]))
    except Exception:
        return redirect("settz")
    concerts = Concert.objects.filter(dateandtime__gte=timezone.now()).order_by("dateandtime")
    print(request.user.groups.filter(name="event-manager").exists())
    print(concerts)
    print(bool(concerts))
    return render(
        request,
        "signup/index.html",
        {
            "concerts": concerts,
            "ismanager": request.user.groups.filter(name="event-manager").exists(),
            "concertsexist": bool(concerts),
        },
    )


def settz(request):
    if request.method == "GET":
        return render(request, "account/choosetz.html")
    if request.method == "POST":
        tzs: dict[str, str] = {"Austin": "America/Chicago", "Auckland": "Pacific/Auckland", "Seoul": "Asia/Seoul", "New York": "America/New_York"}
        request.session["USER_TIMEZONE"] = tzs[request.POST.get("tz")]
        return redirect("signup-index")


def listconcert(request):
    """
    Show list of concerts in the future and in the past. Add signup links.
    If concertmanager, show buttons to add concerts.
    """
    try:
        if request.session["USER_TIMEZONE"]:
            timezone.activate(pytz.timezone(request.session["USER_TIMEZONE"]))
    except Exception:
        return redirect("settz")
    # list concerts in 2 sections
    upcoming = Concert.objects.filter(dateandtime__gte=timezone.now()).order_by("dateandtime")
    previous = Concert.objects.filter(dateandtime__lt=timezone.now()).order_by("dateandtime")
    return render(
        request,
        "signup/listconcert.html",
        {
            "upcoming": upcoming,
            "previous": previous,
            "ismanager": request.user.groups.filter(name="event-manager").exists(),
            "concertsexist": bool(upcoming),
            "locale": request.session["USER_TIMEZONE"]
        },
    )


@login_required()
def createconcert(request):
    """
    Create a concert with a date, a title, a time, description, etc.
    """
    tzs: dict[str, str] = {"Austin": "America/Chicago", "Auckland": "Pacific/Auckland"}
    try:
        if request.session["USER_TIMEZONE"]:
            timezone.activate(pytz.timezone(request.session["USER_TIMEZONE"]))
    except Exception:
        return redirect("settz")
    if request.method == "GET":
        # Only allow event managers to create concerts
        if not request.user.groups.filter(name="event-manager").exists():
            # TODO replace with better error page
            raise PermissionDenied()
        return render(request=request, template_name="signup/createconcert.html")
    if request.method == "POST":
        if not request.user.groups.filter(name="event-manager").exists():
            # Only allow event managers to create concerts
            raise PermissionDenied()
        eventmanager = request.user
        dateandtimeraw: str = request.POST.get("datetime")
        print(dateandtimeraw)
        location = request.POST.get("location")
        maxduration = request.POST.get("maxtime")
        description: str | None = request.POST.get("description")
        piano = bool(request.POST.get("piano"))
        signuplink: str | None = request.POST.get("signuplink")
        title: str | None = request.POST.get("title")
        title = title if title else "Project Melody"
        userselectedtz = request.POST.get("timezone")
        timez = pytz.timezone(tzs[userselectedtz])
        timezone.activate(timez)
        dateandtime: datetime = datetime.fromisoformat(dateandtimeraw)
        dateandtime = timez.localize(dateandtime)
        # dateandtime = dateandtime.replace(tzinfo=timez)
        print(dateandtime.tzinfo)
        print(dateandtime)
        newconcert = Concert(
            title=title,
            location=location,
            dateandtime=dateandtime,
            maxtime=maxduration,
            piano=piano,
            description=description,
            signuplink=signuplink,
        )
        newconcert.save()
        newconcert.manager.set([eventmanager])
        newconcert.save()
        messages.success(request, "Created new concert!")
        return redirect("concertpage", newconcert.id)
    return None


@login_required
def newperformance(request, concert_id):
    """
    Person signup for a concert.
    """
    lockerror = False
    concert = Concert.objects.filter(id=concert_id)
    if not concert:
        return render(request, "404.html")

    concert: Concert = concert[0]
    if concert.signuplink:
        return render(request, "404.html")
    # check if concert is locked
    iseventmanager = request.user.groups.filter(name="event-manager").exists()
    # Only event managers can signup for locked concerts
    if concert.locked and not iseventmanager:
        lockerror = True
    totaltimes = 0
    for performance in concert.performance_set.all():
        totaltimes += performance.duration
    # Check concert date
    if concert.dateandtime < timezone.now():
        concert.locked = True
        concert.save()

    if totaltimes >= concert.maxtime and not iseventmanager:
        concert.locked = True
        concert.save()
        lockerror = True
    if lockerror:
        return render(request, "error/concertlocked.html")

    if request.method == "GET":
        # get list of users
        performers = User.objects.all().order_by("last_name").values()
        return render(
            request,
            "signup/newperformance.html",
            {
                "concert": concert,
                "performers": performers,
                "iseventmanager": iseventmanager,
            },
        )
    if request.method == "POST":
        # print(request.POST)
        performers_raw = request.POST.getlist("performers")
        #print(type(performers_raw))
        #print("Performers " + str(performers_raw))
        performers = []
        for performer in performers_raw:
            print(performer)
            performers.append(User.objects.get(id=performer))
        piece = request.POST.get("piece")
        composer = request.POST.get("composer")
        arranger = request.POST.get("arranger")
        duration = request.POST.get("duration")
        comment = request.POST.get("comment")
        # Whatif some fields are missing?
        if not duration or not composer or not piece or not performers:
            messages.error(
                request,
                "Please check that required fields are filled out.",
            )
        # check performance time validity
        if int(duration) + totaltimes >= concert.maxtime + 10 and not iseventmanager:
            # deny
            messages.warning(
                request,
                "Your performance was too long and so it was rejected automatically!",
            )
        if iseventmanager and int(duration) + totaltimes >= concert.maxtime:
            concert.locked = True
            concert.save()
        performance = Performance(
            concert=concert,
            piece=piece,
            composer=composer,
            arranger=arranger,
            duration=int(duration),
            comment=comment,
        )
        performance.save()
        performance.performer.set(performers)
        messages.success(request, "You successfully requested a performance!")
        return redirect("concertpage", concert_id=concert_id)


@login_required()
def concertpage(request, concert_id):
    """
    Show concert details + list of performances
    """
    try:
        if request.session["USER_TIMEZONE"]:
            timezone.activate(pytz.timezone(request.session["USER_TIMEZONE"]))
    except Exception:
        return redirect("settz")
    try:
        concert = Concert.objects.get(id=concert_id)
    except ObjectDoesNotExist:
        return render(request, "404.html")
    if concert.dateandtime < timezone.now():
        concert.locked = True
        concert.save()
    print(concert.dateandtime.tzinfo)
    print(concert.dateandtime)
    useriseventmanager = False
    if request.user.groups.filter(name="event-manager").exists():
        useriseventmanager = True
    return render(
        request,
        "signup/concertpage.html",
        {"concert": concert, "useriseventmanager": useriseventmanager},
    )


@login_required()
def editconcert(request, concert_id):
    """
    Lets ONLY EVENT MANAGERS edit a concert.
    """
    try:
        if request.session["USER_TIMEZONE"]:
            timezone.activate(pytz.timezone(request.session["USER_TIMEZONE"]))
    except Exception:
        return redirect("settz")
    try:
        concert = Concert.objects.get(id=concert_id)
    except ObjectDoesNotExist:
        return render(request, "404.html")
    if not request.user.groups.filter(name="event-manager").exists():
        raise PermissionDenied()
    if request.method == "GET":
        return render(
            request, "signup/createconcert.html", {"edit": True, "concert": concert}
        )

    dateandtimeraw = request.POST.get("datetime")
    userselectedtz = request.POST.get("timezone")
    tzs: dict[str, str] = {"Austin": "America/Chicago", "Auckland": "Pacific/Auckland", "Seoul": "Asia/Seoul", "New York": "America/New_York"}
    timez = pytz.timezone(tzs[userselectedtz])
    timezone.activate(timez)
    dateandtime: datetime = datetime.fromisoformat(dateandtimeraw)
    dateandtime = timez.localize(dateandtime)
    location = request.POST.get("location")
    maxduration = request.POST.get("maxtime")
    description = request.POST.get("description")
    piano = bool(request.POST.get("piano"))
    signuplink = request.POST.get("signuplink")
    title = request.POST.get("title")
    if not dateandtime or not location or not maxduration:
        messages.error(request, "Please fill out all required fields.")
        return redirect("editconcert", concert_id=concert_id)
    concert.dateandtime = dateandtime
    concert.location = location
    concert.maxtime = int(maxduration)
    concert.description = description
    concert.piano = piano
    concert.signuplink = signuplink
    concert.title = title
    concert.save()
    totaltimes = 0
    for performance in concert.performance_set.all():
        totaltimes += performance.duration
    if totaltimes < int(maxduration) or concert.dateandtime < timezone.now():
        concert.locked = False
        concert.save()
    return redirect("concertpage", concert_id=concert_id)


@login_required()
def deleteconcert(request, concert_id):
    """
    Delete a concert
    """
    try:
        concert = Concert.objects.get(id=concert_id)
    except ObjectDoesNotExist:
        return render(request, "404.html")
    # Only event managers can delete concert.
    if not request.user.groups.filter(name="event-manager").exists():
        raise PermissionDenied()
    concert.delete()
    messages.success(request, "Concert deleted successfully!")
    return redirect("signup-index")


@login_required()
def lockconcert(request, concert_id):
    """
    Manual Lock a concert.
    """
    if request.method == "POST":
        return render(request, "error/teapot.html")
    try:
        concert = Concert.objects.get(id=concert_id)
    except ObjectDoesNotExist:
        return render(request, "404.html")
    if not request.user.groups.filter(name="event-manager").exists():
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
    """
    List of concerts a user has signed up for.
    """
    # find user's concert
    try:
        if request.session["USER_TIMEZONE"]:
            timezone.activate(pytz.timezone(request.session["USER_TIMEZONE"]))
    except Exception:
        return redirect("settz")
    allconcerts = Concert.objects.all()
    userconcerts = []
    for concert in allconcerts:
        performances = concert.performance_set.filter(performer=request.user)
        if performances:
            userconcerts.append(concert)
    return render(
        request,
        "signup/listconcert.html",
        {"myconcert": True, "concerts": userconcerts, "locale": request.session["USER_TIMEZONE"]},
    )


def concertjson(request):
    """
    API to get a list of concerts in json format.
    """
    if request.method == "POST":
        return render(request, "error/teapot.html")
    try:
        if request.session["USER_TIMEZONE"]:
            timezone.activate(pytz.timezone(request.session["USER_TIMEZONE"]))
    except Exception:
        return redirect("settz")
    loggedin = bool(request.user)
    # get start and end dates
    print(type(request.GET.get("start")))
    start = request.GET.get("start")
    end = request.GET.get("end")
    if start and end:
        start = datetime.fromisoformat(start)
        end = datetime.fromisoformat(end)
        concerts_temp = Concert.objects.filter(
            dateandtime__gt=start, dateandtime__lt=end
        )
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
    return render(
        request,
        "signup/concerts.json",
        {
            "concerts": concerts,
            "loggedin": loggedin
        },
        content_type="application/json",
    )


def calendar(request):
    """
    Display a calendar with concerts on it.
    """
    if request.method == "POST":
        return render(request, "error/teapot.html")
    return render(request, "signup/calendar.html")


@login_required()
def editperformance(request, concert_id, performance_id):
    """
    Edit a performance.
    """
    try:
        concert = Concert.objects.get(id=concert_id)
        performance = Performance.objects.get(id=performance_id)
        if performance.concert != concert:
            return render(request, "404.html")
    except ObjectDoesNotExist:
        return render(request, "404.html")
    if concert.signuplink:
        return render(request, "404.html")
    iseventmanager = request.user.groups.filter(name="event-manager").exists()
    if not (
        iseventmanager
        or performance.performer.filter(id=request.user.id).exists()
    ):
        raise PermissionDenied()
    totaltimes = 0
    for performancex in concert.performance_set.all():
        totaltimes += performancex.duration
    if request.method == "GET":
        performers = User.objects.all().order_by("last_name").values()
        performanceperformers = performance.performer.all().values_list("id", flat=True)
        print(performance.performer.all())
        return render(
            request,
            "signup/editperformance.html",
            {
                "edit": True,
                "concert": concert,
                "performance": performance,
                "performers": performers,
                "performanceperformers": performanceperformers,
                "isedit": True,
            },
        )
    performers_raw = request.POST.getlist("performers")
    performers = []
    for performer in performers_raw:
        print(performer)
        performers.append(User.objects.get(id=performer))
    piece = request.POST.get("piece")
    composer = request.POST.get("composer")
    arranger = request.POST.get("arranger")
    duration = request.POST.get("duration")
    comment = request.POST.get("comment")
    if not duration or not composer or not piece or not performers:
        print(f"{composer} {duration} {piece} {performers}")
        return HttpResponse("Please Fill Out All Required Fields")
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
    print(comment)
    performance.save()
    if iseventmanager and int(duration) + totaltimes >= concert.maxtime:
        concert.locked = True
        concert.save()
    return HttpResponse("Performance edited successfully.")


def deleteperformance(request, concert_id, performance_id):
    """
    Delete a performance.
    """
    try:
        concert = Concert.objects.get(id=concert_id)
        performance = Performance.objects.get(id=performance_id)
    except ObjectDoesNotExist:
        return render(request, "404.html")
    if concert.signuplink:
        return render(request, "404.html")
    # iseventmanager = request.user.groups.filter(name="event-manager").exists()
    if not (
        request.user.groups.filter(name="event-manager").exists()
        or performance.performer.filter(id=request.user.id).exists()
    ):
        raise PermissionDenied()
    performance.delete()
    messages.success(request, "Performance deleted successfully!")
    return redirect("concertpage", concert_id=concert.id)
