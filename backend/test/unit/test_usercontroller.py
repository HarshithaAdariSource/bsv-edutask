import pytest
from unittest.mock import Mock
from src.controllers.usercontroller import UserController


@pytest.fixture
def mock_dao():
    return Mock()

@pytest.fixture
def user_controller(mock_dao):
    return UserController(mock_dao)


# case1: Valid email, single user
def test_get_user_by_email_single_user(user_controller, mock_dao):
    mock_user = {"email": "test@example.com"}
    mock_dao.find.return_value = [mock_user]

    result = user_controller.get_user_by_email("test@example.com")

    assert result == mock_user

# case2: Valid email, multiple users
def test_get_user_by_email_multiple_users(user_controller, mock_dao, capsys):
    mock_user1 = {"email": "test@example.com"}
    mock_user2 = {"email": "test@example.com"}
    mock_dao.find.return_value = [mock_user1, mock_user2]
    result = user_controller.get_user_by_email("test@example.com")
    captured = capsys.readouterr()
    assert result == mock_user1
    assert "more than one user found" in captured.out

# case3: Valid email, no users
def test_get_user_by_email_no_user(user_controller, mock_dao):
    mock_dao.find.return_value = []
    result = user_controller.get_user_by_email("test@example.com")
    assert result is None

# case4: Empty email
def test_get_user_by_email_empty_email(user_controller):
    with pytest.raises(ValueError):
        user_controller.get_user_by_email("")

# case5: Invalid email (no @)
def test_get_user_by_email_invalid_email_format(user_controller):
    with pytest.raises(ValueError):
        user_controller.get_user_by_email("abc.com")

# case6: Invalid email (missing domain)
def test_get_user_by_email_missing_domain(user_controller, mock_dao): 
    mock_dao.find.return_value = [] 
    with pytest.raises(ValueError): 
        user_controller.get_user_by_email("abc@")

# case7: DAO exception
def test_get_user_by_email_dao_exception(user_controller, mock_dao):
    mock_dao.find.side_effect = Exception("DB failure")
    with pytest.raises(Exception):
        user_controller.get_user_by_email("test@example.com")