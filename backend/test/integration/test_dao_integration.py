import pytest
from unittest.mock import patch
from pymongo.errors import WriteError
from src.util.dao import DAO

TEST_COLLECTION = "test_users"


# Fixture: DAO with mocked validator
@pytest.fixture
def dao():
    with patch("src.util.dao.getValidator") as mock_validator:
        mock_validator.return_value = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["name", "active"],
                "properties": {
                    "name": {"bsonType": "string"},
                    "active": {"bsonType": "bool"},
                }
            }
        }
        dao = DAO(TEST_COLLECTION)
        dao.drop()
        dao = DAO(TEST_COLLECTION)
        yield dao
        dao.drop()

# case 1: Successful creation
def test_create_valid_data(dao):
    data = {"name": "Alice", "active": True}

    result = dao.create(data)

    assert result is not None
    assert "_id" in result
    assert result["name"] == "Alice"
    assert result["active"] is True


# case 2: Missing required field
def test_create_missing_required_field(dao):
    data = {"name": "Alice"} # missing 'active' field
    with pytest.raises(WriteError):
        dao.create(data)

# case 3: Invalid data type
def test_create_invalid_type(dao):
    data = {"name": "Alice", "active": "yes"}  # active should be a boolean
    with pytest.raises(WriteError):
        dao.create(data)

# case 4: Extra field
def test_create_extra_field_allowed(dao):
    data = {"name": "Alice", "active": True, "extra": "allowed"}
    result = dao.create(data)
    assert result["extra"] == "allowed"

# case 5: Persistence check
def test_create_persists_in_db(dao):
    data = {"name": "Bob", "active": False}
    created = dao.create(data)
    obj_id = created["_id"]["$oid"]
    fetched = dao.findOne(obj_id)
    assert fetched["name"] == "Bob"
    assert fetched["active"] is False


# case 6: Duplicate values
def test_create_duplicate(dao):
    data1 = {"name": "Alice", "active": True}
    data2 = {"name": "Alice", "active": True}
    dao.create(data1)
    with pytest.raises(WriteError):
        dao.create(data2)