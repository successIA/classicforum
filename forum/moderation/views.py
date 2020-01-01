from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .events import (
    create_moderator_added_event,
    create_moderator_removed_event,
    create_category_changed_event
)
from ..comments.models import Comment
from .mixins import staff_member_required
from .models import Moderator, ModeratorEvent
from .forms import ModeratorForm

User = get_user_model()


@login_required
@staff_member_required
def create_moderator(request):
    context = {"form": ModeratorForm}
    if request.method == "POST":
        form = ModeratorForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data.get("user")
            cats = form.cleaned_data.get("categories")
            mod, created = Moderator.objects.get_or_create(user=user)
            mod.categories.add(*cats)
            create_moderator_added_event(user, cats)
            messages.success(
                request, f"<strong>{user.username}</strong> is now a moderator!"
            )
            return redirect("moderation:moderator_list")
        else:
            context["form"] = form
            context["prev_cats"] = form.cleaned_data.get("categories")
    return render(request, "moderation/moderator_edit.html", context)


@login_required
@staff_member_required
def update_moderator(request, username):
    user = get_object_or_404(User, username=username)
    mod = get_object_or_404(Moderator, user=user)
    # queryset must be evaluated here
    prev_cats = list(mod.categories.all())
    form = ModeratorForm(instance=mod)
    if request.method == "POST":
        form = ModeratorForm(request.POST, instance=mod)
        if form.is_valid():
            cats = form.cleaned_data.get("categories")
            mod.categories.clear()
            mod.categories.add(*cats)
            curr_cats = mod.categories.all()
            create_category_changed_event(user, prev_cats, curr_cats)
            messages.success(
                request, 
                f"<strong>{user.username}</strong>'s categories field"
                 " was updated successfully"
            )
            return redirect("moderation:moderator_list")
    context = {"moderator": mod, "form": form, "prev_cats": prev_cats}
    return render(request, "moderation/moderator_edit.html", context)


@login_required
@staff_member_required
def delete_moderator(request, username):
    if request.method == "POST":
        mod = get_object_or_404(Moderator, user__username=username)
        user = mod.user
        # queryset must be evaluated here
        cats = list(mod.categories.all())
        mod.delete()
        create_moderator_removed_event(user, cats)
        messages.success(
            request, 
            f"<strong>{user.username}</strong> is no longer a moderator!"
        )
        return redirect("moderation:moderator_list")


@login_required
@staff_member_required
def moderator_list(request):
    moderators = Moderator.objects.select_related("user").all()
    return render(
        request, "moderation/moderator_list.html", {"moderators": moderators}
    )


@login_required
@staff_member_required
def moderator_detail(request, username):
    user = get_object_or_404(User, username=username)
    mod = get_object_or_404(Moderator, user=user)
    context = {"user": user, "moderator": mod}
    return render(request, "moderation/moderator_detail.html", context)
