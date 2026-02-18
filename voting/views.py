from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from events.models import Event, Category, Participation, UserEventRole
from .models import Vote, VoteFinalization

def get_user_role(user, event):
    # Retrieve the role object to check permissions
    try:
        return UserEventRole.objects.get(user=user, event=event)
    except UserEventRole.DoesNotExist:
        return None

@login_required
def vote_category(request, event_id, category_id):
    event = get_object_or_404(Event, pk=event_id)
    category = get_object_or_404(Category, pk=category_id, event=event)

    if not event.is_voting_open:
        messages.error(request, "A szavazás lezárult.")
        return redirect('event_detail', event_id=event.id)
    
    user_role = get_user_role(request.user, event)
    
    can_vote = False
    if user_role:
        if user_role.is_zsuri or user_role.is_domst:
            can_vote = True
    
    # Superuser handling: they can see the page if they want (maybe to debug), 
    # but actual voting should probably be restricted to those who have the role, 
    # or we let admin vote if they really want to?
    # The previous logic said "Adminisztrátorként nem szavazhatsz, csak ha Zsűri jogkört is kapsz."
    # So we stick to that.
    
    if not can_vote:
        if user_role and user_role.is_dok:
             messages.warning(request, "A DÖK tagjai csak az eredményeket láthatják.")
             return redirect('event_detail', event_id=event.id)
        
        # If user is admin but has no voting rights
        if request.user.is_superuser:
            messages.error(request, "Adminisztrátorként nem szavazhatsz, csak ha Zsűri jogkört is kapsz.")
            return redirect('event_detail', event_id=event.id)
            
        messages.error(request, "Nincs jogosultságod megtekinteni ezt az oldalt.")
        return redirect('home')

    participations_qs = Participation.objects.filter(event=event).select_related('osztaly', 'country')
    
    # Check if already finalized
    is_finalized = VoteFinalization.objects.filter(user=request.user, category=category).exists()
    
    existing_votes = Vote.objects.filter(user=request.user, category=category)
    vote_dict = {v.participation.id: v.rank for v in existing_votes}

    # Sort participations by existing rank, or default ordering
    participations = list(participations_qs)
    # Put ranked items first, sorted by rank. Unranked items at the end, sorted by defaults.
    # Actually, if there are votes, all items should have a rank theoretically if fully voted, 
    # or partial votes.
    # If partial, ranked ones come first.
    def get_rank(p):
        return vote_dict.get(p.id, 999999) # unranked go to end
    
    participations.sort(key=get_rank)
    # If no votes yet, it falls back to whatever stable sort, probably by ID or insertion if get_rank returns same for all.
    # To be deterministic, secondary sort by ID.
    participations.sort(key=lambda p: (get_rank(p), p.osztaly.tagozat)) 

    if request.method == 'POST':
        if is_finalized:
             messages.error(request, "A szavazásod már véglegesítve lett ebben a kategóriában.")
             return redirect('vote_category', event_id=event.id, category_id=category.id)

        action = request.POST.get('action')
        
        # New logic: receive ordered list of participation IDs
        order_str = request.POST.get('order', '')
        if not order_str:
            if action == 'autosave':
                from django.http import JsonResponse
                return JsonResponse({'status': 'error', 'message': 'No order data'})
            messages.error(request, "Hiba történt a sorrend mentésekor.")
            return redirect('vote_category', event_id=event.id, category_id=category.id)
            
        ordered_ids = [int(x) for x in order_str.split(',') if x]
        
        # Verify all participations for this event are present
        current_p_ids = set(p.id for p in participations)
        submitted_p_ids = set(ordered_ids)

        # Save/Update votes based on index
        for index, p_id in enumerate(ordered_ids):
            if p_id in current_p_ids:
                rank = index + 1
                Vote.objects.update_or_create(
                    user=request.user,
                    category=category,
                    participation_id=p_id,
                    defaults={'rank': rank}
                )
        
        # Handle autosave (AJAX request)
        if action == 'autosave':
            from django.http import JsonResponse
            return JsonResponse({'status': 'success', 'message': 'Mentve'})

        if action == 'finalize':
            # Check implicit: if user dragged everything, there are ranks for everything.
            # Just ensure we have votes for all participations.
            count_votes = Vote.objects.filter(user=request.user, category=category).count()
            count_parts = participations_qs.count()
            
            if count_votes != count_parts:
                 messages.error(request, "Rendszerhiba: nem mindenki kapott helyezést ({}/{})".format(count_votes, count_parts))
                 return redirect('vote_category', event_id=event.id, category_id=category.id)
            
            VoteFinalization.objects.create(user=request.user, category=category)
            messages.success(request, "Szavazatok véglegesítve!")
            
            # Check for next unfinalized category
            all_categories = event.categories.all()
            for cat in all_categories:
                if not VoteFinalization.objects.filter(user=request.user, category=cat).exists():
                    messages.info(request, f"Következő kategória: {cat.name}")
                    return redirect('vote_category', event_id=event.id, category_id=cat.id)
            
            # All categories finalized
            messages.success(request, "Minden kategóriát véglegesítettél!")
            return redirect('event_detail', event_id=event.id)
            
        messages.success(request, "Sorrend mentve.")
        return redirect('vote_category', event_id=event.id, category_id=category.id)

    # Get event admins and superusers for contact info
    from django.contrib.auth.models import User
    event_admins = UserEventRole.objects.filter(
        event=event,
        is_admin=True
    ).select_related('user')
    
    system_admins = User.objects.filter(is_superuser=True)
    
    context = {
        'event': event,
        'category': category,
        'participations': participations,
        'vote_dict': vote_dict,
        'is_finalized': is_finalized,
        'event_admins': event_admins,
        'system_admins': system_admins,
    }
    return render(request, 'voting/vote.html', context)
