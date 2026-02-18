from django.contrib import admin
from .models import Event, Category, Participation, UserEventRole
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
import secrets
import string

class CategoryInline(admin.TabularInline):
    model = Category
    extra = 1

class ParticipationInline(admin.TabularInline):
    model = Participation
    extra = 1
    autocomplete_fields = ['osztaly', 'country']


class UserEventRoleInline(admin.TabularInline):
    model = UserEventRole
    extra = 1
    autocomplete_fields = ['user']

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'event_type', 'is_public', 'is_voting_open', 'description_short')
    list_filter = ('event_type', 'is_public', 'is_voting_open', 'date')
    search_fields = ('name', 'description')
    inlines = [CategoryInline, ParticipationInline, UserEventRoleInline]
    
    def description_short(self, obj):
        return (obj.description[:50] + '...') if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'event')
    list_filter = ('event',)
    search_fields = ('name', 'event__name')

@admin.register(Participation)
class ParticipationAdmin(admin.ModelAdmin):
    list_display = ('event', 'osztaly', 'country')
    list_filter = ('event',)
    search_fields = ('event__name', 'osztaly__tagozat', 'country__name')
    autocomplete_fields = ['osztaly', 'country']

@admin.register(UserEventRole)
class UserEventRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'is_zsuri', 'is_dok', 'is_domst', 'is_admin')
    list_filter = ('event', 'is_zsuri', 'is_dok', 'is_domst', 'is_admin')
    list_editable = ('is_zsuri', 'is_dok', 'is_domst', 'is_admin')
    autocomplete_fields = ['user', 'event']
    search_fields = ('user__username', 'event__name')
    ordering = ('event', 'user')
    list_per_page = 50
    fields = ('user', 'event', 'is_zsuri', 'is_dok', 'is_domst', 'is_admin', 'context')
    actions = ['send_credentials_to_selected', 'open_mailto_for_selected']
    
    def send_credentials_to_selected(self, request, queryset):
        """Send login credentials to selected users with their roles"""
        success_count = 0
        error_count = 0
        
        for user_role in queryset:
            try:
                user = user_role.user
                event = user_role.event
                
                # Generate new password
                alphabet = string.ascii_letters + string.digits
                new_password = ''.join(secrets.choice(alphabet) for i in range(12))
                
                # Set new password
                user.set_password(new_password)
                user.save()
                
                # Collect roles
                roles = []
                if user_role.is_zsuri:
                    roles.append('Zsűri')
                if user_role.is_dok:
                    roles.append('DÖK')
                if user_role.is_domst:
                    roles.append('DÖMST')
                if user_role.is_admin:
                    roles.append('Esemény Adminisztrátor')
                
                roles_text = ', '.join(roles) if roles else 'Nincs megadva'
                
                # Compose email
                subject = f"SZLG ZSŰRI Meghívás - {event.name}"
                message = (
                    f"Tisztelt {user.first_name or user.username}!\n\n"
                    f"Kiválasztották a következő szerepkör(ök)re az alábbi eseményhez:\n\n"
                    f"Esemény: {event.name}\n"
                    f"Dátum: {event.date.strftime('%Y. %B %d. %H:%M')}\n"
                    f"Szerepkör(ök): {roles_text}\n\n"
                    f"Bejelentkezési adatok:\n"
                    f"Felhasználónév: {user.username}\n"
                    f"Jelszó: {new_password}\n\n"
                    f"Kérem, lépjen be itt: {request.build_absolute_uri('/')}\n\n"
                    f"Üdvözlettel,\n"
                    f"SZLG Zsűri Rendszer"
                )
                
                # Send email
                if user.email:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=False
                    )
                    success_count += 1
                else:
                    error_count += 1
                    self.message_user(
                        request,
                        f"Hiányzó email cím: {user.username}",
                        level=messages.WARNING
                    )
                    
            except Exception as e:
                error_count += 1
                self.message_user(
                    request,
                    f"Hiba történt {user_role.user.username} esetében: {str(e)}",
                    level=messages.ERROR
                )
        
        if success_count > 0:
            self.message_user(
                request,
                f"Sikeresen elküldve {success_count} felhasználónak.",
                level=messages.SUCCESS
            )
        if error_count > 0:
            self.message_user(
                request,
                f"{error_count} felhasználónak nem sikerült elküldeni.",
                level=messages.WARNING
            )
    
    send_credentials_to_selected.short_description = "Bejelentkezési adatok küldése kijelölt felhasználóknak"
    
    def open_mailto_for_selected(self, request, queryset):
        """Generate mailto links for selected users"""
        from django.template.response import TemplateResponse
        from urllib.parse import quote
        
        mailto_data = []
        
        for user_role in queryset:
            user = user_role.user
            event = user_role.event
            
            if not user.email:
                continue
            
            # Generate new password
            alphabet = string.ascii_letters + string.digits
            new_password = ''.join(secrets.choice(alphabet) for i in range(12))
            
            # Set new password
            user.set_password(new_password)
            user.save()
            
            # Collect roles
            roles = []
            if user_role.is_zsuri:
                roles.append('Zsűri')
            if user_role.is_dok:
                roles.append('DÖK')
            if user_role.is_domst:
                roles.append('DÖMST')
            if user_role.is_admin:
                roles.append('Esemény Adminisztrátor')
            
            roles_text = ', '.join(roles) if roles else 'Nincs megadva'
            
            # Compose email
            subject = f"Meghívás - {event.name}"
            body = (
                f"Szia {user.first_name or user.username}!\n\n"
                f"Kiválasztottak a következő szerepkör(ök)re az alábbi eseményhez:\n\n"
                f"Esemény: {event.name}\n"
                f"Dátum: {event.date.strftime('%Y. %B %d. %H:%M')}\n"
                f"Szerepkör(ök): {roles_text}\n\n"
                f"Bejelentkezési adatok:\n"
                f"Felhasználónév: {user.username}\n"
                f"Jelszó: {new_password}\n\n"
                f"Kérlek, lépj be itt: {request.build_absolute_uri('/')}\n\n"
                f"Üdvözlettel,\n"
                f"SZLG Zsűri Rendszer"
            )
            
            mailto_link = f"mailto:{user.email}?subject={quote(subject)}&body={quote(body)}"
            
            mailto_data.append({
                'user': user,
                'email': user.email,
                'mailto_link': mailto_link,
                'password': new_password,
            })
        
        if not mailto_data:
            self.message_user(
                request,
                "Nincs érvényes email címmel rendelkező felhasználó a kiválasztottak között.",
                level=messages.WARNING
            )
            return
        
        context = {
            **self.admin_site.each_context(request),
            'title': 'Email hivatkozások',
            'mailto_data': mailto_data,
            'opts': self.model._meta,
        }
        
        return TemplateResponse(request, 'admin/events/mailto_links.html', context)
    
    open_mailto_for_selected.short_description = "Mailto hivatkozások megnyitása kijelölt felhasználóknak"
