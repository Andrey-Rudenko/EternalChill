from django.urls import path
from .views import home, RegisterView, users_list, send_friendship_request, following_list, profile, \
    cancel_friendship_request, reject_friendship_request, accept_friend, friends, unfriend, posts, create_post, chat
urlpatterns = [
    path('', home, name='users-home'),
    path('register/', RegisterView.as_view(), name='users-register'),
    path('profile/', profile, name='users-profile'),
    path('users/', users_list, name='users_list'),
    path('users/friendship/add_friend/<username>/', send_friendship_request, name='add_friend'),
    path('following/', following_list, name='following_list'),
    path('profile/<username>/', profile, name='profile'),
    path('friendship/cancel/<username>', cancel_friendship_request, name='cancel_fr_request'),
    path('friendship/reject/<username>', reject_friendship_request, name='reject_fr_request'),
    path('friendship/accept/<username>', accept_friend, name='accept_friend'),
    path('friendship/unfriend/<username>', unfriend, name='unfriend'),
    path('friends/<username>', friends, name='friends'),
    path('posts', posts, name='posts'),
    path('createpost', create_post, name='create_post'),
    path('chat', chat, name='chat'),
]
