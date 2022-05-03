from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import View
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from users.models import Profile, Post, Chat
from django.contrib.auth.models import User
from .forms import RegisterForm, LoginForm, UpdateUserForm, UpdateProfileForm, NewPost, NewMessage

from friendship.exceptions import AlreadyExistsError
from friendship.models import Friend, FriendshipRequest


def home(request):
    return render(request, 'users/home.html')


class RegisterView(View):
    form_class = RegisterForm
    initial = {'key': 'value'}
    template_name = 'users/register.html'

    def dispatch(self, request, *args, **kwargs):
        # will redirect to the home page if a user tries to access the register page while logged in
        if request.user.is_authenticated:
            return redirect(to='/')

        # else process dispatch as it otherwise normally would
        return super(RegisterView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            form.save()

            username = form.cleaned_data.get('username')
            messages.success(request, f'Аккаунт {username} создан')

            return redirect(to='/')

        return render(request, self.template_name, {'form': form})


class CustomLoginView(LoginView):
    form_class = LoginForm

    def form_valid(self, form):
        remember_me = form.cleaned_data.get('remember_me')

        if not remember_me:
            # set session expiry to 0 seconds. So it will automatically close the session after the browser is closed.
            self.request.session.set_expiry(0)

            # Set session as modified to force data updates/cookie to be saved.
            self.request.session.modified = True

        # else browser session will be as long as the session cookie time "SESSION_COOKIE_AGE" defined in settings.py
        return super(CustomLoginView, self).form_valid(form)


class ChangePasswordView(SuccessMessageMixin, PasswordChangeView):
    template_name = 'users/change_password.html'
    success_message = "Пароль изменён"
    success_url = reverse_lazy('users-home')


def posts(request):
    all_posts = Post.objects.all()
    context = {
        "all_posts": all_posts,
    }
    return render(request, 'users/posts.html', context)


@login_required
def users_list(request):
    avatars = Profile.objects.all()
    user_form = User.objects.all()
    context = {
        'ava': avatars,
        'info': user_form,
    }
    return render(request, 'users/users_list.html', context)


@login_required
def send_friendship_request(request, username):
    user = User.objects.get(username=username)
    Friend.objects.add_friend(request.user, user)
    return redirect("/profile/" + user.username)


@login_required
def cancel_friendship_request(request, username):
    user = User.objects.get(username=username)
    request_filter = \
        list(filter(lambda x: x.from_user_id == request.user.id, Friend.objects.unrejected_requests(user=user)))
    request_filter[0].cancel()
    return redirect("/following/")


@login_required
def reject_friendship_request(request, username):
    user = User.objects.get(username=username)
    request_filter = \
        list(filter(lambda x: x.from_user_id == user.id, Friend.objects.unrejected_requests(user=request.user)))
    request_filter[0].cancel()
    return redirect("/following/")


@login_required
def accept_friend(request, username):
    user = User.objects.get(username=username)
    request_filter = \
        list(filter(lambda x: x.from_user_id == user.id, Friend.objects.unrejected_requests(user=request.user)))
    request_filter[0].accept()
    return redirect("/following/")


@login_required
def unfriend(request, username):
    user = User.objects.get(username=username)
    Friend.objects.remove_friend(request.user, user)
    return redirect("/profile/" + user.username)


@login_required
def following_list(request):
    you_requests = Friend.objects.sent_requests(user=request.user)
    to_you_requests = Friend.objects.unrejected_requests(user=request.user)
    context = {
        "you_requests": you_requests,
        'to_you_requests': to_you_requests,
    }
    return render(request, 'users/following_list.html', context)


@login_required
def create_post(request):
    if request.method == 'POST':
        form = NewPost(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect("/posts")
    return render(request, "users/create_post.html", {"form": NewPost})


@login_required
def profile(request, username):
    user = User.objects.get(username=username)
    if request.user == user:
        if request.method == 'POST':
            user_form = UpdateUserForm(request.POST, instance=request.user)
            profile_form = UpdateProfileForm(request.POST, request.FILES, instance=request.user.profile)

            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                messages.success(request, 'Профиль успешно обновлён')
                return redirect("/profile/" + user.username)
        else:
            user_form = UpdateUserForm(instance=request.user)
            profile_form = UpdateProfileForm(instance=request.user.profile)

        return render(request, 'users/profile.html', {'user_form': user_form, 'profile_form': profile_form})
    else:
        is_friend = Friend.objects.are_friends(request.user, user)
    friend_request = ""
    request_id = None
    if not is_friend:
        request_filter = \
            list(filter(lambda x: x.from_user_id == user.id, Friend.objects.unrejected_requests(user=request.user)))
        if request_filter:
            friend_request = "them"
            request_id = request_filter[0].id
        request_filter = \
            list(filter(lambda x: x.from_user_id == request.user.id, Friend.objects.unrejected_requests(user=user)))
        if request_filter:
            friend_request = "you"
            request_id = request_filter[0].id
    return render(request, "users/profile_all.html",
                  {"other_user": user, "friends": is_friend, "friend_request": friend_request,
                   "request_id": request_id})


@login_required
def friends(request, username):
    user = User.objects.get(username=username)
    friend_list = Friend.objects.friends(user)
    avatars = Profile.objects.all()
    user_form = User.objects.all()
    context = {
        'ava': avatars,
        'info': user_form,
        'other_user': user,
        'friends': friend_list,
    }
    return render(request, "users/friends.html", context)


@login_required
def chat(request):
    all_message = Chat.objects.all()
    if request.method == 'POST':
        form = NewMessage(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            # return redirect("/chat")
    context = {
        "all_message": all_message,
        'form': NewMessage,
    }
    return render(request, 'users/chat.html', context)
