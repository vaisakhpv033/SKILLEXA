import pytest
import json
from rest_framework import status
from accounts.models import User
from courses.models import Topics
from rest_framework_simplejwt.tokens import RefreshToken

@pytest.fixture
def create_users(db):
    """ Fixture to create admin and regular users """
    admin = User.objects.create_superuser(
        email="admin@example.com",
        username="adminuser",
        password="AdminPass123",
        first_name="Admin",
        last_name="User",
        is_active=True,
    )
    user = User.objects.create_user(
        email="user@example.com",
        username="testuser",
        password="UserPass123",
        first_name="Test",
        last_name="User",
        is_active=True,
    )

    return admin, user

@pytest.fixture
def create_topics(db):
    """ Fixture to create test topics """
    main_topic = Topics.objects.create(name="Programming")
    sub_topic = Topics.objects.create(name="Python", parent=main_topic)
    return main_topic, sub_topic

@pytest.fixture
def auth_headers(create_users):
    """ Fixture to generate auth headers """
    admin, user = create_users
    return {
        "admin": {"HTTP_AUTHORIZATION": f"Bearer {RefreshToken.for_user(admin).access_token}"},
        "user": {"HTTP_AUTHORIZATION": f"Bearer {RefreshToken.for_user(user).access_token}"},
    }

@pytest.mark.django_db
def test_list_topics(client, create_topics):
    """ Anyone can list topics """
    response = client.get("/course/topics/")
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
def test_retrieve_topic(client, create_topics):
    """ Retrieve a single topic with subcategories """
    main_topic, _ = create_topics
    response = client.get(f"/course/topics/{main_topic.id}/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == "Programming"

@pytest.mark.django_db
def test_create_topic_as_admin(client, create_topics, auth_headers):
    """ Admin can create a topic """
    main_topic, _ = create_topics
    data = {"name": "Web Development", "parent": main_topic.id}
    response = client.post("/course/topics/", data, **auth_headers["admin"])
    assert response.status_code == status.HTTP_201_CREATED

@pytest.mark.django_db
def test_create_topic_as_user_forbidden(client, create_topics, auth_headers):
    """ Regular users cannot create topics """
    data = {"name": "Web Development"}
    response = client.post("/course/topics/", data, **auth_headers["user"])
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
def test_update_topic_as_admin(client, create_topics, auth_headers):
    """ Admin can update a topic """
    _, sub_topic = create_topics
    data = {"name": "Advanced Python"}
    response = client.patch(
        f"/course/topics/{sub_topic.id}/",
        data=json.dumps(data),  # Convert dictionary to JSON string
        content_type="application/json",  # Specify content type
        **auth_headers["admin"]
    )
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
def test_delete_topic_as_admin(client, create_topics, auth_headers):
    """ Admin can delete a topic if it has no subcategories """
    _, sub_topic = create_topics
    response = client.delete(f"/course/topics/{sub_topic.id}/", **auth_headers["admin"])
    assert response.status_code == status.HTTP_204_NO_CONTENT
