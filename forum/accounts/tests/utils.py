def login(test_case, username, password):
    logged_in = test_case.client.login(username=username, password=password)
    test_case.assertTrue(logged_in)

def make_superuser(username):
    from test_plus import TestCase

    user = TestCase().make_user(username)
    user.is_superuser = True
    user.save()
    
    return user
