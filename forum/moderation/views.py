from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import (
    get_object_or_404, 
    Http404,
    HttpResponseRedirect,
    redirect, 
    render,
)

from .events import (
    create_moderator_added_event,
    create_moderator_removed_event,
    create_category_changed_event
)
from ..comments.models import Comment
from .mixins import (
    staff_member_required,
    supermoderator_or_moderator_owner_required,
    hide_post_permission_required,
    unhide_post_permission_required
)
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
            mod = Moderator.objects.create(user=user)
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
@supermoderator_or_moderator_owner_required
def moderator_detail(request, username, mod_profile=None):
    mod_profile.user = mod_profile.user
    hidden_threads = mod_profile.hidden_threads.get_related().all()
    hidden_comments = mod_profile.hidden_comments.select_related(
        "user", "category", "thread"
    ).all()
    context = {
        "mod_profile": mod_profile,
        "hidden_threads": hidden_threads,
        "hidden_comments": hidden_comments,
    }
    return render(request, "moderation/moderator_detail.html", context)


@login_required
@hide_post_permission_required
def hide_thread(request, slug, thread=None, mod=None):
    if request.method == "POST":
        with transaction.atomic():
            thread.visible = False
            thread.save()
            mod.hidden_threads.add(thread)
            ModeratorEvent.objects.create(
                event_type=ModeratorEvent.THREAD_HIDDEN,
                user=request.user,
                thread=thread,
            )
        messages.success(
            request, f"<strong>{thread.title}</strong> has been"
            " hidden successfully"
        )
        return redirect(mod)
    raise Http404


@login_required
@unhide_post_permission_required
def unhide_thread(request, slug, thread=None, mod=None):
    if request.method == "POST":
        with transaction.atomic():
            thread.visible = True
            thread.save()
            for mod in Moderator.objects.all():
                mod.hidden_threads.remove(thread)
            ModeratorEvent.objects.create(
                event_type=ModeratorEvent.THREAD_UNHIDDEN,
                user=request.user,
                thread=thread,
            )
        messages.success(
            request, f"<strong>{thread.title}</strong> is now visible to all users"
        )
        return HttpResponseRedirect(thread.get_absolute_url())
    raise Http404


@login_required
@hide_post_permission_required
def hide_comment(request, thread_slug, comment_pk, comment=None, mod=None):
    if request.method == "POST":
        redirect_to = comment.get_url_for_next_or_prev()
        with transaction.atomic():
            comment.hide()
            mod.hidden_comments.add(comment)
            ModeratorEvent.objects.create(
                event_type=ModeratorEvent.COMMENT_HIDDEN,
                user=request.user,
                comment=comment,
            )
        messages.success(
            request, f"<strong>{comment.user.username}</strong>'s comment hidden"
                      " successfully!"
        )
        return redirect(redirect_to)
    raise Http404


@login_required
@unhide_post_permission_required
def unhide_comment(request, thread_slug, comment_pk, comment=None, mod=None):
    if request.method == "POST":
        with transaction.atomic():
            comment.unhide()
            for mod in Moderator.objects.all():
                mod.hidden_comments.remove(comment)
            ModeratorEvent.objects.create(
                event_type=ModeratorEvent.COMMENT_UNHIDDEN,
                user=request.user,
                comment=comment,
            )
        messages.success(
            request, f"<strong>{comment.user.username}</strong>'s comment"
                     " is now visible to all users"
        )
        return redirect(comment.get_precise_url())
    raise Http404
