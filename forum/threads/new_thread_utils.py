# from forum.accounts.models import Followership


# def new_thread_and_comments_decider(self=None, thread_qs=None):
#     for thread in thread_qs:
#         if self.request.user.is_authenticated and thread in self.request.user.userprofile.followed_threads.all():
#             '''
#             check if there is a signed in user and check if the user is following the thread
#             '''

#             # obtain the user's thread followership
#             users_followership = Followership.objects.get(userprofile=self.request.user.userprofile, thread=thread)

#             # obtain the user's last seen which is associated with the thread
#             last_seen = users_followership.last_seen

#             # print('last seen from cat detail: ', last_seen.strftime("%Y-%m-%d %H:%M:%S"))
#             # comment_qs = thread.comment_set.all().filter(comment__created__gt=last_seen)
#             # print(comment_qs)
#             new_comment = None
#             counter = -1
#             for comment in thread.comment_set.all():
#                 '''
#                 Loop through all the comments belonging to the thread
#                 '''

#                 if comment.created is not None:
#                     # print(comment, ' :', comment.created)
#                     # Take account of number of comments before new comments
#                     # The counter adds 1 when it about to enter the if statement below
#                     # which will make the the old comments count to be one greater than
#                     # the actual count. to solve this the counter starts from -1
#                     counter = counter + 1
#                     print(comment.created)
#                     if comment.created > last_seen:
#                         print('HIIIIIT')
#                         '''
#                         If the commentcreated datetime is greater than the user's
#                         last seen with respect to the current thread initialise the
#                         comment to another variable then break out of the loop
#                         '''

#                         new_comment = comment
#                         # print('new comment: ', new_comment.id)

#                         # break out of this block
#                         break
#             if new_comment:
#                 '''
#                 If there is a new comment in the current thread, set the current thread's
#                 get_absolute_url method to the precise url that will link the user to
#                 the first new comment
#                 '''

#                 # Get the unread comments by substracting the old comments count
#                 # from the total comments count
#                 num_of_unread_comments = thread.comment_set.count() - counter

#                 precise_url = thread.get_absolute_url()
#                 precise_url = precise_url + '#comment' + str(new_comment.id)
#                 thread.get_absolute_url = precise_url
#                 thread.count = num_of_unread_comments

#                 # print('precise url: ', thread.get_absolute_url)
#                 # print(thread_qs.first().get_absolute_url())
#     # for thread in list(thread_qs):
#     #     print('thread abs_url: ', thread.get_absolute_url)

#     '''
#     thread_qs is a list which retains any methods or attributes modified earlier by
#     not query db any time it is called
#     thread_qs.all() will simply query the db again because it holds an object
#     of category.thread_set.all() which is hooked up to the db
#     '''
#     return thread_qs
