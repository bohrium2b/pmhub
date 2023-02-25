from django.db import models
from django.contrib.auth.models import User

# Create your models here.


"""
Create custom model for Performer (user).
"""
class Performer(models.Model):
    """
    This model defines a performer (user) with an instrument.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    instruments = models.TextField(blank=True)



class Concert(models.Model):
    """
    Model: Concert
    -----
    This model defines a concert with a dedicated event manager(s), a location, a date and time, a maximum length of time, the availability of piano, description, etc.
    """
    manager = models.ManyToManyField(User, blank=True)
    location = models.TextField()
    dateandtime = models.DateTimeField()
    maxtime = models.IntegerField()
    piano = models.BooleanField()
    locked = models.BooleanField(blank = True, default=False)
    description = models.TextField(blank=True)


class Performance(models.Model):
    """
    This model defines a performance with a performer(s), a concert,
    """
    performer = models.ManyToManyField(User, blank=True)
    concert = models.ForeignKey(Concert, on_delete=models.CASCADE)
    piece = models.TextField()
    composer = models.TextField()
    arranger = models.TextField(blank=True)
    duration = models.IntegerField()
    comment = models.TextField(blank=True)



