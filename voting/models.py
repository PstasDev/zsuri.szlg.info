from django.db import models
from django.contrib.auth.models import User
from events.models import Category, Participation

class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Szavazó")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Kategória")
    participation = models.ForeignKey(Participation, on_delete=models.CASCADE, verbose_name="Produkció")
    rank = models.PositiveIntegerField(verbose_name="Helyezés") 

    class Meta:
        unique_together = ('user', 'category', 'participation')
        ordering = ['rank']
        verbose_name = "Szavazat"
        verbose_name_plural = "Szavazatok"

    def __str__(self):
        return f"{self.user} - {self.category} - {self.rank}."

class VoteFinalization(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Felhasználó")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Kategória")
    finalized_at = models.DateTimeField(auto_now_add=True, verbose_name="Véglegesítve")

    class Meta:
        unique_together = ('user', 'category')
        verbose_name = "Véglegesítés"
        verbose_name_plural = "Véglegesítések"

    def __str__(self):
        return f"{self.user} - {self.category} Véglegesítve"
