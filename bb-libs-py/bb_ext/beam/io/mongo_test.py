import apache_beam as beam
import mock
import mongomock
import pymongo
from toolz.dicttoolz import dissoc

from bb_ext.beam.io.mongo import MongoBulkWriteFn


@mock.patch('pymongo.MongoClient')
def test_insert(mock_client_class):
    mock_mongo_client = mongomock.MongoClient()
    mock_client_class.return_value = mock_mongo_client

    INPUT_DOCS = [{
        'name': 'A'
    }, {
        'name': 'B'
    }]

    (INPUT_DOCS
     | beam.transforms.Map(lambda d: pymongo.InsertOne(d))
     | beam.transforms.ParDo(
         MongoBulkWriteFn(
             db_uri='mongodb://localhost/db',
             collection_name='test_beam',
             db_name='db',
             order_writes=True)))

    found_objs = mock_mongo_client.get_database('db')['test_beam'].find({})
    no_id_objs = map(lambda o: dissoc(o, '_id'), found_objs)
    assert no_id_objs == INPUT_DOCS
