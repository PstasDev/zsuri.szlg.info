from django.contrib import admin
from .models import Osztaly, Country
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django import forms
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.utils import timezone
import secrets

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
    actions = ('delete_selected', 'issue_event_passwords')
    
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

    @admin.action(description='Új jelszó generálása és küldése a kijelölt felhasználóknak')
    def issue_event_passwords(self, request, queryset):
        """Reset selected users' passwords, email them individually, and show them once."""
        results = []
        timestamp = timezone.localtime(timezone.now()) if settings.USE_TZ else timezone.now()

        for user in queryset.order_by('pk'):
            result = {
                'user': user,
                'email': user.email,
                'password': None,
                'status': '',
                'status_level': 'warning',
            }

            if not user.email:
                result['status'] = 'Nem történt jelszócsere: nincs email-cím megadva.'
                results.append(result)
                continue

            # 24 random bytes provide 192 bits of entropy; URL-safe characters are
            # also easy to copy from the admin results table.
            password = secrets.token_urlsafe(24)

            try:
                user.set_password(password)
                user.save(update_fields=('password',))
                result['password'] = password

                context = {
                    'user': user,
                    'password': password,
                    'login_url': 'https://zsuri.szlg.info/',
                    'timestamp': timestamp,
                    'current_year': timestamp.year,
                }
                text_body = render_to_string('emails/user_event_credentials.txt', context)
                html_body = render_to_string('emails/user_event_credentials.html', context)
                email = EmailMultiAlternatives(
                    subject='Új bejelentkezési adatok – SZLG Zsűri Rendszer',
                    body=text_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[user.email],
                )
                email.attach_alternative(html_body, 'text/html')
                if email.send() == 1:
                    result['status'] = 'A jelszó megváltozott, az email sikeresen elküldve.'
                    result['status_level'] = 'success'
                else:
                    result['status'] = 'A jelszó megváltozott, de az email küldése nem sikerült.'
            except Exception:
                # Keep the generated password visible to the admin for this response
                # if it was already set, without exposing mail-server errors.
                result['status'] = 'A jelszó beállítása vagy az email küldése nem sikerült.'

            results.append(result)

        context = {
            **self.admin_site.each_context(request),
            'title': 'Új bejelentkezési adatok',
            'results': results,
            'opts': self.model._meta,
        }
        response = TemplateResponse(request, 'admin/core/user_password_results.html', context)
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        return response

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
