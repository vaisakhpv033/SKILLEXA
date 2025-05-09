from django.urls import path

from .views import (
    ActivateUserView,
    AdminUserDetailView,
    AdminUserListView,
    BlockUserView,
    UnblockUserView,
)

urlpatterns = [
    path("users/", AdminUserListView.as_view(), name="admin-user-list"),
    path("users/<int:id>/", AdminUserDetailView.as_view(), name="admin-user-detail"),
    path("users/<int:id>/block/", BlockUserView.as_view(), name="admin-block-user"),
    path(
        "users/<int:id>/unblock/", UnblockUserView.as_view(), name="admin-unblock-user"
    ),
    path(
        "users/<int:id>/activate/",
        ActivateUserView.as_view(),
        name="admin-activate-user",
    ),
]
