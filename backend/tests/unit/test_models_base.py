# backend/tests/unit/test_models_base.py
"""Tests for app.models.base — the PyObjectId Pydantic v2 integration, the trickiest piece of the models/ layer."""

import pytest
from bson import ObjectId
from pydantic import BaseModel, ValidationError

from app.models.base import PyObjectId, MongoBaseModel


class _SampleDoc(MongoBaseModel):
    name: str


class TestPyObjectIdValidation:
    def test_accepts_a_real_objectid_instance(self):
        oid = ObjectId()

        class M(BaseModel):
            model_config = {"arbitrary_types_allowed": True}
            id: PyObjectId

        m = M(id=oid)
        assert m.id == oid

    def test_accepts_a_valid_objectid_hex_string(self):
        oid_str = str(ObjectId())

        class M(BaseModel):
            model_config = {"arbitrary_types_allowed": True}
            id: PyObjectId

        m = M(id=oid_str)
        assert isinstance(m.id, ObjectId)
        assert str(m.id) == oid_str

    def test_rejects_an_invalid_string(self):
        class M(BaseModel):
            model_config = {"arbitrary_types_allowed": True}
            id: PyObjectId

        with pytest.raises(ValidationError):
            M(id="not-a-valid-objectid")

    def test_rejects_a_random_integer(self):
        class M(BaseModel):
            model_config = {"arbitrary_types_allowed": True}
            id: PyObjectId

        with pytest.raises(ValidationError):
            M(id=12345)


class TestMongoBaseModelIdField:
    def test_generates_a_default_id_when_not_provided(self):
        doc = _SampleDoc(name="test")
        assert isinstance(doc.id, ObjectId)

    def test_accepts_id_via_alias_underscore_id(self):
        oid = ObjectId()
        doc = _SampleDoc(**{"_id": oid, "name": "test"})
        assert doc.id == oid

    def test_accepts_id_via_field_name_directly(self):
        # populate_by_name=True is what enables this — Motor gives us
        # `_id`, but our own service code often constructs with `id=`.
        oid = ObjectId()
        doc = _SampleDoc(id=oid, name="test")
        assert doc.id == oid

    def test_two_default_generated_ids_are_different(self):
        assert _SampleDoc(name="a").id != _SampleDoc(name="b").id


class TestToMongoSerialization:
    def test_to_mongo_keeps_id_as_objectid_not_string(self):
        doc = _SampleDoc(name="test")
        mongo_dict = doc.to_mongo()
        assert isinstance(mongo_dict["_id"], ObjectId)

    def test_to_mongo_uses_underscore_id_key_not_id(self):
        doc = _SampleDoc(name="test")
        mongo_dict = doc.to_mongo()
        assert "_id" in mongo_dict
        assert "id" not in mongo_dict

    def test_json_serialization_converts_id_to_string(self):
        doc = _SampleDoc(name="test")
        json_str = doc.model_dump_json(by_alias=True)
        assert str(doc.id) in json_str