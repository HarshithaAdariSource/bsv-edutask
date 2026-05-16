import pytest
from unittest.mock import patch
from pymongo.errors import WriteError
from src.util.dao import DAO

TEST_COLLECTION = "integration_test_collection"


# ---------------------------------------------------------------------------
# Pytest fixture
# ---------------------------------------------------------------------------
# The fixture has two jobs:
#   (1) replace the production validator with a controlled mocked schema, so
#       this test is not affected by changes in the validator JSON files,
#   (2) provide a clean test collection that does not interfere with
#       production data.
# ---------------------------------------------------------------------------
@pytest.fixture
def dao():
    mocked_validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["name", "active"],
            "properties": {
                "name": {
                    "bsonType": "string",
                    "description": "name must be a string and is required",
                    "uniqueItems": True,
                },
                "active": {
                    "bsonType": "bool",
                    "description": "active must be a boolean and is required",
                },
            },
        }
    }

    with patch("src.util.dao.getValidator") as mock_get_validator:
        mock_get_validator.return_value = mocked_validator

        bootstrap = DAO(TEST_COLLECTION)
        bootstrap.collection.drop()

        sut = DAO(TEST_COLLECTION)
        yield sut
        sut.collection.drop()

# TC1 - EC1 (valid input, all constraints satisfied)
def test_create_valid_data(dao):
    data = {"name": "Alice", "active": True}
    result = dao.create(data)
    assert result is not None
    assert "_id" in result
    assert result["name"] == "Alice"
    assert result["active"] is True


# TC2 - EC2 (missing required field "active")
def test_create_missing_required_field(dao):
    data = {"name": "Alice"}
    with pytest.raises(WriteError):
        dao.create(data)


# TC3 - EC3 (wrong bsonType for "active": string instead of bool)
def test_create_invalid_type(dao):
    data = {"name": "Alice", "active": "yes"}
    with pytest.raises(WriteError):
        dao.create(data)


# TC4 - EC4 (extra field not declared in schema)
def test_create_extra_field_allowed(dao):
    data = {"name": "Alice", "active": True, "extra": "allowed"}
    result = dao.create(data)
    assert result["extra"] == "allowed"


# TC5 - EC1 + persistence boundary
def test_create_persists_in_db(dao):
    data = {"name": "Bob", "active": False}
    created = dao.create(data)
    obj_id = created["_id"]["$oid"]
    fetched = dao.findOne(obj_id)
    assert fetched["name"] == "Bob"
    assert fetched["active"] is False


# TC6 - EC5 (uniqueItems violation: two documents with the same "name")
def test_create_duplicate(dao):
    data1 = {"name": "Alice", "active": True}
    data2 = {"name": "Alice", "active": True}
    dao.create(data1)
    with pytest.raises(WriteError):
        dao.create(data2)