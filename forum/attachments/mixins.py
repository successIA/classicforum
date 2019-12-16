from django.http import HttpResponseBadRequest


def ajax_required(function):
    def wrap(request, *args, **kwargs):
        # print('post received in mixin')
        # if not request.is_ajax():
        #     print('bad request')
        #     return HttpResponseBadRequest()
        return function(request, *args, **kwargs)
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap
