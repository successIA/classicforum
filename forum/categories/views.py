from django.views.generic.edit import CreateView, UpdateView
from django.views.generic import DetailView, ListView
from django.views import View
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from forum.categories.models import Category
from forum.categories.utils import get_additional_category_detail_ctx
from forum.threads.forms import ThreadForm
# from forum.threads.views import create_thread


def category_detail(request, slug, filter_str=None, page=1, form=None):
    print('category_detail called: ')
    print('slug: ', slug)
    # form = ThreadForm(request.POST or None)

    # if form.is_valid():
    #     if not request.user.is_authenticated:
    #         raise PermissionDenied
    #     return create_thread(request, form)

    category = get_object_or_404(Category, slug=slug)
    # if not request.method == 'POST':
    if not form:
        form = ThreadForm(initial={'category': category})
    ctx = {
        'category': category,
        'form': form,
    }
    ctx.update(
        get_additional_category_detail_ctx(request, category, filter_str, page)
    )
    return render(request, 'categories/category_detail.html', ctx)

