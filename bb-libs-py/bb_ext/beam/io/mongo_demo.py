import argparse

import apache_beam as beam
import pymongo
from apache_beam.options.pipeline_options import PipelineOptions

from bb_ext.beam.io.mongo import (MongoBulkWriteFn,
                                  ping_mongo_database,
                                  MongoWriteStats)

SAMPLE_DOCS = [
    {'name': 'A'},
    {'name': 'B'},
    {'name': 'C'},
    {'name': 'D'},
]


def main(argv=None):
    parser = argparse.ArgumentParser()

    known_args, pipeline_args = parser.parse_known_args(argv)
    pipeline_options = PipelineOptions(pipeline_args)
    pipeline = beam.Pipeline(options=pipeline_options)

    DB_URI = 'mongodb://localhost/beam_to_mongo_demo'
    ping_mongo_database(DB_URI)

    write_stats = MongoWriteStats('beam_to_mongo_demo')
    (pipeline
        | beam.Create(SAMPLE_DOCS)
        | beam.transforms.Map(lambda d: pymongo.InsertOne(d))
        | beam.transforms.ParDo(MongoBulkWriteFn(DB_URI, collection_name='sample_docs', stats=write_stats)))

    result = pipeline.run()
    result.wait_until_finish()


if __name__ == '__main__':
    main()
