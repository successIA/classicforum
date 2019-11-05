from django.core.urlresolvers import reverse
from django.contrib.auth.models import User


from forum.categories.models import Category
from forum.threads.models import Thread


def sign_up_a_new_user(instance=None, username='ade', password='abcdef123456'):
    if not instance:
        raise ValueError('Instance cannot be None or empty')
    self = instance
    url = reverse('signup')
    data = {
        'username': username,
        'email': username + '@doe.com',
        'password1': 'abcdef123456',
        'password2': 'abcdef123456'
    }
    self.response = self.client.post(url, data)
    return self.response


def create_thread(self, title='Django', description='The Web Framework For The Perfectionist', slug='django'):
    sign_up_a_new_user(self, 'john')
    user = User.objects.get(id=1)
    category = Category.objects.create(title='Django', description='The Web Framework For The Perfectionist', slug='django')
    thread = Thread.objects.create(title='Galaxy S5 Discussion Thread', body='Lorem ipsum dalor', category=self.category, user=user)
    return thread
