from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render

from forum.categories.models import Category
from forum.categories.utils import get_additional_category_detail_ctx
from forum.threads.forms import ThreadForm

# from forum.threads.views import create_thread


def category_detail(request, slug, filter_str=None, page=1, form=None):
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
