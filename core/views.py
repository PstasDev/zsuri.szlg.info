from django.shortcuts import render
from events.models import Event

def home(request):
    from django.utils import timezone
    from datetime import datetime
    now = timezone.now()
    
    # Get the start of the current month
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    all_events = Event.objects.filter(is_public=True).order_by('date')
    
    # Current events: from this month onwards
    current_events = all_events.filter(date__gte=start_of_month)
    # Past events: before this month
    past_events = all_events.filter(date__lt=start_of_month).order_by('-date')
    
    return render(request, 'core/home.html', {
        'current_events': current_events,
        'past_events': past_events
    })
