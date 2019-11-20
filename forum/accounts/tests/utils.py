def login(test_case, username, password):
    logged_in = test_case.client.login(username=username, password=password)
    test_case.assertTrue(logged_in)
