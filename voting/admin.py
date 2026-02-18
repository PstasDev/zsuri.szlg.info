from django.contrib import admin
from .models import Vote, VoteFinalization

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'participation', 'rank')
    list_filter = ('category', 'user')
    search_fields = ('user__username', 'category__name')
    list_per_page = 50

@admin.register(VoteFinalization)
class VoteFinalizationAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'finalized_at')
    list_filter = ('category', 'user')
    search_fields = ('user__username', 'category__name')
