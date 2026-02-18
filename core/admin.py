from django.contrib import admin
from .models import Osztaly, Country
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django import forms
import secrets
import string

# Define a custom form for creating users without a password
class PasswordLessUserCreationForm(forms.ModelForm):
    password = forms.CharField(required=False, widget=forms.PasswordInput, help_text="Hagyja üresen automatikus generáláshoz.")
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name')
        labels = {
            'first_name': 'Teljes Név',
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if not password:
            alphabet = string.ascii_letters + string.digits
            password = ''.join(secrets.choice(alphabet) for i in range(12))
            user.set_password(password)
        else:
            user.set_password(password)
        if commit:
            user.save()
        return user

class UserAdmin(BaseUserAdmin):
    add_form = PasswordLessUserCreationForm
    
    # Customize list display
    list_display = ('username', 'email', 'first_name', 'is_staff')
    
    # Customize edit form (change_form)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Személyes adatok', {'fields': ('first_name', 'email')}), # Removed last_name
        ('Jogosultságok', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fontos dátumok', {'fields': ('last_login', 'date_joined')}),
    )
    
    # Customize add form (when adding new user)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'password'),
        }),
    )

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(Osztaly)
class OsztalyAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'startYear', 'tagozat')
    list_filter = ('startYear', 'tagozat')
    ordering = ('-startYear', 'tagozat')
    search_fields = ('startYear', 'tagozat')

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'flag')
    search_fields = ('name',)
    ordering = ('name',)
