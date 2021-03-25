import gzip

from scrapy.exporters import JsonLinesItemExporter


class JsonLinesGzipItemExporter(JsonLinesItemExporter):

    def __init__(self, file, **kwargs):
        gzfile = gzip.GzipFile(fileobj=file)
        super(JsonLinesGzipItemExporter, self).__init__(gzfile, **kwargs)

    def finish_exporting(self):
        self.file.close()
