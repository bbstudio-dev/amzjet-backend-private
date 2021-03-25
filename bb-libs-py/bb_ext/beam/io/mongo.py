import logging
import pymongo

from apache_beam.transforms import DoFn
from apache_beam.metrics import Metrics

from bb_ext.mongo.helpers import auto_reconnect


class MongoWriteStats(object):
    def __init__(self, namespace):
        self.namespace = namespace

        self.inserted_count = Metrics.counter(self.namespace, 'inserted_count')
        self.upserted_count = Metrics.counter(self.namespace, 'upserted_count')
        self.modified_count = Metrics.counter(self.namespace, 'modified_count')
        self.matched_count = Metrics.counter(self.namespace, 'matched_count')
        self.deleted_count = Metrics.counter(self.namespace, 'deleted_count')

    def _update_from_bulk_write_result(self, bulk_api_result):
        self.inserted_count.inc(bulk_api_result.inserted_count)
        self.upserted_count.inc(bulk_api_result.upserted_count)
        self.modified_count.inc(bulk_api_result.modified_count)
        self.matched_count.inc(bulk_api_result.matched_count)
        self.deleted_count.inc(bulk_api_result.deleted_count)


def ping_mongo_database(db_uri):
    logging.info('Pinging MongoDB <%s>.' % db_uri)
    client = pymongo.MongoClient(db_uri)
    client.get_database().command('ping')


class MongoBulkWriteFn(DoFn):
    """
    Sends bulk write operations (e.g. pymongo.UpdateOne) from the input PCollection
    to the MongoDb server.
    """

    # TODO: Consider the following improvements:
    # - Schema validation
    # - Handling AutoReconnect error
    # - Max number of allowed errors

    def __init__(self,
                 db_uri,
                 collection_name,
                 db_name=None,
                 max_batch_size=100,
                 order_writes=False,
                 stats=None):
        self.db_uri = db_uri

        self.db_name = db_name
        self.collection_name = collection_name
        self.max_batch_size = max_batch_size
        self.order_writes = order_writes

        self.stats = stats

        self._client = None

        self._reset()

    def start_bundle(self):
        """Called by the runtime before a bundle of elements is processed on a worker."""

        self._reset()

    def finish_bundle(self):
        """Called by the runtime after a bundle of elements is processed on a worker."""

        self._flush()

    def process(self, element):
        """Called by the runtime to process each element in a bundle."""

        if len(self._batch) >= self.max_batch_size:
            self._flush()

        self._batch.append(element)

    def _collection(self):
        client = self._get_or_create_client()

        # If self.db_name is None, the client will return the default
        # database if specified in the database URI.
        db = client.get_database(self.db_name)

        return db[self.collection_name]

    def _reset(self):
        self._batch = []

    @auto_reconnect
    def _flush(self):
        if len(self._batch) > 0:
            try:
                logging.debug(
                    'Writing batch of %d elements.' % len(self._batch))
                result = self._collection().bulk_write(
                    self._batch, ordered=self.order_writes)
                if self.stats:
                    self.stats._update_from_bulk_write_result(result)
            except pymongo.errors.BulkWriteError as ex:
                logging.exception(ex)
                raise

        self._reset()

    def _get_or_create_client(self):
        if self._client is None:
            self._client = pymongo.MongoClient(self.db_uri)

        return self._client

    def display_data(self):
        return {'db_uri': self.db_uri, 'collection_name': self.collection_name}
