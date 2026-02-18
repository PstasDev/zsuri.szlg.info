from django.db import models
from datetime import datetime

class Osztaly(models.Model):
    startYear = models.IntegerField(null=False, blank=False)
    tagozat = models.CharField(max_length=1, null=False, blank=False)

    class Meta:
        ordering = ['-startYear', 'tagozat']
        verbose_name = "Osztály"
        verbose_name_plural = "Osztályok"

    def __str__(self):
        current_year = datetime.now().year
        current_month = datetime.now().month
        school_year = current_year
        if current_month < 9:
            school_year -= 1

        graduation_year = self.startYear + 4
        if self.tagozat in ['A', 'E', 'F']:
            graduation_year += 1

        if school_year >= graduation_year:
            return f"{graduation_year}{self.tagozat}"
        else:
            years_passed = school_year - self.startYear
            if self.tagozat in ['A', 'E', 'F']:
                if years_passed == 0:
                    return f"KNY{self.tagozat}" if self.tagozat == 'A' else f"NY{self.tagozat}"
                else:
                    return f"{8 + years_passed}. {self.tagozat}"
            else:
                return f"{9 + years_passed}. {self.tagozat}"

class Country(models.Model):
    name = models.CharField(max_length=100)
    flag = models.CharField(max_length=10, blank=True, null=True, help_text="Emoji flag")

    class Meta:
        ordering = ['name']
        verbose_name = "Ország"
        verbose_name_plural = "Országok"

    def __str__(self):
        return self.name
