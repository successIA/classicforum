

# def split_string(function):
#     def wrapper():
#         func = function()
#         splitted_string = func.split()
#         return splitted_string
#     return wrapper


# def uppercase_decorator(function):
#     def wrapper():
#         string = function()
#         make_uppercase = string.upper()
#         return make_uppercase
#     return wrapper


# @split_string
# @uppercase_decorator
# def say_hi():
#     return 'hello there'


# # decorate = uppercase_decorator(say_hi)
# # print(decorate())
# print(say_hi())


# def decorator_with_arguments(function):
#     def wrapper_accepting_arguments(arg1, arg2):
#         print('My arguments are: {0}, {1} '.format(arg1, arg2))
#         function(arg1, arg2)
#     return wrapper_accepting_arguments


# @decorator_with_arguments
# def cities(city_one, city_two):
#     print("Cities I love are {0} and {1}".format(city_one, city_two))


# cities("Nairobi", "Accra")


# def a_decorator_with_arbitrary_arguments(function_to_decorate):
#     def a_wrapper_accepting_arbitrary_arguments(*args, **kwargs):
#         print("The positional arguments are", args)
#         print("The positional arguments are", kwargs)
#         function_to_decorate(*args, **kwargs)
#     return a_wrapper_accepting_arbitrary_arguments


# @a_decorator_with_arbitrary_arguments
# def function_with_no_arguments(a,b,c, first_name, last_name):
#     print(a, b, c, first_name, last_name)


# function_with_no_arguments(1, 2, 3, first_name='Derrick', last_name='Mwiti')


import functools


def decorator_maker_with_arguments(decorator_arg1, decorator_arg2, decorator_arg3):

    def decorator(func):

        @functools.wraps(func)
        def wrapper(function_arg1, function_arg2, function_arg3) :
            "This is the wrapper function"
            print("The wrapper can access all the variables\n"
                  "\t- from the decorator maker: {0} {1} {2}\n"
                  "\t- from the function call: {3} {4} {5}\n"
                  "and pass them to the decorated function"
                  .format(decorator_arg1, decorator_arg2,decorator_arg3,
                          function_arg1, function_arg2,function_arg3))
            return func(function_arg1, function_arg2,function_arg3)

        return wrapper

    return decorator

pandas = "Pandas"
@decorator_maker_with_arguments(pandas, "Numpy","Scikit-learn")
def decorated_function_with_arguments(function_arg1, function_arg2,function_arg3):
    print("This is the decorated function and it only knows about its arguments: {0}"
           " {1}" " {2}".format(function_arg1, function_arg2,function_arg3))

decorated_function_with_arguments(pandas, "Science", "Tools")
print('decorated_function_with_arguments.__name__: ', decorated_function_with_arguments.__name__)
print('decorated_function_with_arguments.__doc__: ', decorated_function_with_arguments.__doc__)


def decorator_maker_with_arguments(decorator_arg1, decorator_arg2, decorator_arg3):

    def decorator(func):
        
        def wrapper(function_arg1, function_arg2, function_arg3) :
            "This is the wrapper function"
            print("The wrapper can access all the variables\n"
                  "\t- from the decorator maker: {0} {1} {2}\n"
                  "\t- from the function call: {3} {4} {5}\n"
                  "and pass them to the decorated function"
                  .format(decorator_arg1, decorator_arg2,decorator_arg3,
                          function_arg1, function_arg2,function_arg3))
            return func(function_arg1, function_arg2,function_arg3)
        wrapper.__doc__ = func.__doc__
        wrapper.__name__ = func.__name__
        return wrapper

    return decorator

pandas = "Pandas"
@decorator_maker_with_arguments(pandas, "Numpy","Scikit-learn")
def decorated_function_with_arguments(function_arg1, function_arg2,function_arg3):
    print("This is the decorated function and it only knows about its arguments: {0}"
           " {1}" " {2}".format(function_arg1, function_arg2,function_arg3))

decorated_function_with_arguments(pandas, "Science", "Tools")
print('decorated_function_with_arguments.__name__: ', decorated_function_with_arguments.__name__)
print('decorated_function_with_arguments.__doc__: ', decorated_function_with_arguments.__doc__)
