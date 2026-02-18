from django.db import models
from django.contrib.auth.models import User
from core.models import Osztaly, Country

class Event(models.Model):
    TYPE_CHOICES = (
        ('GOLYABAL', 'Gólyabál'),
        ('UNESCO', 'UNESCO'),
        ('CUSTOM', 'Egyéb'),
    )
    name = models.CharField(max_length=200, verbose_name="Esemény neve")
    date = models.DateTimeField(verbose_name="Dátum")
    event_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='CUSTOM', verbose_name="Típus")
    is_public = models.BooleanField(default=True, verbose_name="Nyilvános (Látható)")
    is_voting_open = models.BooleanField(default=False, verbose_name="Szavazás Nyitva")
    description = models.TextField(blank=True, verbose_name="Leírás")

    class Meta:
        verbose_name = "Esemény"
        verbose_name_plural = "Események"

    def __str__(self):
        return self.name

class UserEventRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Felhasználó")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name="Esemény")
    is_zsuri = models.BooleanField(default=False, verbose_name="Zsűri")
    is_dok = models.BooleanField(default=False, verbose_name="DÖK")
    is_domst = models.BooleanField(default=False, verbose_name="DÖMST")
    is_admin = models.BooleanField(default=False, verbose_name="Admin")
    context = models.TextField(blank=True, verbose_name="Megjegyzés (Admin)", help_text="Belső megjegyzés adminisztrátorok számára")

    class Meta:
        unique_together = ('user', 'event')
        verbose_name = "Felhasználó Jogosultság"
        verbose_name_plural = "Felhasználó Jogosultságok"

    def __str__(self):
        roles = []
        if self.is_zsuri: roles.append('Zsűri')
        if self.is_dok: roles.append('DÖK')
        if self.is_domst: roles.append('DÖMST')
        if self.is_admin: roles.append('Admin')
        return f"{self.user} - {self.event}: {', '.join(roles)}"

class Category(models.Model):
    event = models.ForeignKey(Event, related_name='categories', on_delete=models.CASCADE, verbose_name="Esemény")
    name = models.CharField(max_length=100, verbose_name="Kategória neve")
    
    class Meta:
        verbose_name = "Kategória"
        verbose_name_plural = "Kategóriák"

    def __str__(self):
        return f"{self.event.name} - {self.name}"

class Participation(models.Model):
    event = models.ForeignKey(Event, related_name='participations', on_delete=models.CASCADE, verbose_name="Esemény")
    osztaly = models.ForeignKey(Osztaly, on_delete=models.CASCADE, verbose_name="Osztály")
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Ország (UNESCO)")
    
    class Meta:
        unique_together = ('event', 'osztaly')
        verbose_name = "Induló / Produkció"
        verbose_name_plural = "Indulók / Produkciók"

    def __str__(self):
        if self.country:
            return f"{self.osztaly} - {self.country}"
        return f"{self.osztaly}"
