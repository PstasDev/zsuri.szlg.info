from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Event, UserEventRole, Category
from django.contrib.auth.decorators import login_required
from voting.models import VoteFinalization, Vote

def get_user_capabilities(user, event):
    caps = {
        'can_vote': False,
        'can_see_overall': False,
        'can_see_detailed': False,
        'is_admin': user.is_superuser,
    }
    
    try:
        role = UserEventRole.objects.get(user=user, event=event)
        if role.is_admin:
            caps['is_admin'] = True
            caps['can_see_detailed'] = True
            caps['can_see_overall'] = True
        if role.is_zsuri:
            caps['can_vote'] = True
        if role.is_dok:
             caps['can_see_overall'] = True
        if role.is_domst:
            caps['can_vote'] = True
            caps['can_see_overall'] = True
            caps['can_see_detailed'] = True
    except UserEventRole.DoesNotExist:
        pass

    if user.is_superuser:
        caps['can_see_detailed'] = True
        caps['can_see_overall'] = True
        caps['is_admin'] = True

    return caps

@login_required
def event_detail(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    
    caps = get_user_capabilities(request.user, event)

    categories = event.categories.all()
    categories_status = []
    

from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
import secrets
import string

@login_required
def event_detail(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    
    caps = get_user_capabilities(request.user, event)

    categories = event.categories.all()
    categories_status = []
    
    for category in categories:
        is_finalized = VoteFinalization.objects.filter(user=request.user, category=category).exists()
        categories_status.append({
            'category': category,
            'is_finalized': is_finalized
        })

    context = {
        'event': event,
        'categories_status': categories_status,
        'caps': caps,
    }
    return render(request, 'events/detail.html', context)


@login_required
def event_admin_dashboard(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    caps = get_user_capabilities(request.user, event)
    
    if not caps['is_admin']:
        messages.error(request, "Nincs jogosultságod az esemény adminisztrálásához.")
        return redirect('event_detail', event_id=event.id)
        
    user_roles = UserEventRole.objects.filter(event=event).select_related('user')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        
        if action == 'send_credentials' and user_id:
            try:
                target_user = User.objects.get(pk=user_id)
                
                # Generate password: 12 chars, alphanumeric
                alphabet = string.ascii_letters + string.digits
                new_password = ''.join(secrets.choice(alphabet) for i in range(12))
                
                target_user.set_password(new_password)
                target_user.save()
                
                # Send email logic
                email_subject = f"Bejelentkezési adatok - {event.name}"
                email_message = (
                    f"Szia {target_user.first_name}!\n\n"
                    f"Az alábbi adatokkal tudsz bejelentkezni a(z) {event.name} zsűrizéséhez:\n\n"
                    f"Felhasználónév (Email): {target_user.email}\n"
                    f"Jelszó: {new_password}\n\n"
                    f"Kérlek, lépj be itt: {request.build_absolute_uri('/')}\n\n"
                    f"Üdvözlettel,\nSZLG Zsűri Rendszer"
                )
                
                try:
                    send_mail(
                        email_subject,
                        email_message,
                        settings.DEFAULT_FROM_EMAIL,
                        [target_user.email],
                        fail_silently=False
                    )
                    messages.success(request, f"E-mail elküldve {target_user.email} címre.")
                except Exception as e:
                    messages.warning(request, f"Jelszó beállítva, de e-mail hiba: {str(e)}")
                    # Show password on screen if email fails
                    messages.info(request, f"A generált jelszó: {new_password}")

            except User.DoesNotExist:
                messages.error(request, "Felhasználó nem található.")
        
        return redirect('event_admin_dashboard', event_id=event.id)

    context = {
        'event': event,
        'user_roles': user_roles,
    }
    return render(request, 'events/admin_dashboard.html', context)


@login_required
def event_results_overall(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    caps = get_user_capabilities(request.user, event)
    
    if not caps['can_see_overall']:
        messages.error(request, "Nincs jogosultságod az eredmények megtekintéséhez.")
        return redirect('event_detail', event_id=event.id)
    
    categories = event.categories.all()
    results = []
    
    for category in categories:
        # Calculate average ranks for each participation
        from django.db.models import Avg
        votes = Vote.objects.filter(category=category).values('participation').annotate(avg_rank=Avg('rank')).order_by('avg_rank')
        
        category_results = []
        for vote_data in votes:
            participation = get_object_or_404(event.participations, pk=vote_data['participation'])
            category_results.append({
                'participation': participation,
                'avg_rank': round(vote_data['avg_rank'], 2)
            })
        
        results.append({
            'category': category,
            'results': category_results
        })
    
    context = {
        'event': event,
        'results': results,
    }
    return render(request, 'events/results_overall.html', context)


@login_required
def event_results_detailed(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    caps = get_user_capabilities(request.user, event)
    
    if not caps['can_see_detailed']:
        messages.error(request, "Nincs jogosultságod a részletes eredmények megtekintéséhez.")
        return redirect('event_detail', event_id=event.id)
    
    from django.contrib.auth.models import User
    categories = event.categories.all()
    detailed_results = []
    
    # Get all users who voted for this event
    all_users = User.objects.filter(
        vote__category__event=event
    ).distinct().order_by('username')
    
    for category in categories:
        # Get all participations for this event
        participations = event.participations.all().order_by('osztaly')
        
        # Get all users who voted in this category
        category_users = User.objects.filter(
            vote__category=category
        ).distinct().order_by('username')
        
        # Build participation votes matrix
        participation_votes = []
        for participation in participations:
            user_ranks = {}
            votes = Vote.objects.filter(
                category=category,
                participation=participation
            ).select_related('user')
            
            for vote in votes:
                user_ranks[vote.user.id] = vote.rank
            
            participation_votes.append({
                'participation': participation,
                'user_ranks': user_ranks
            })
        
        detailed_results.append({
            'category': category,
            'users': category_users,
            'participation_votes': participation_votes
        })
    
    context = {
        'event': event,
        'detailed_results': detailed_results,
        'all_users': all_users,
    }
    return render(request, 'events/results_detailed.html', context)
