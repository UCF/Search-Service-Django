from rest_framework import parsers

class MultiPartJSONParser(parsers.MultiPartParser):
    def parse(self, stream, *args, **kwargs):
        data = super().parse(stream, *args, **kwargs)

        mutable_data = data.data.copy()
        unmarshalled_blob_names = []
        json_parser = parsers.JSONParser()

        for name, blob in data.files.items():
            if blob.content_type == 'application/json' and name not in data.data:
                mutable_data[name] = json_parser.parse(blob)
                unmarshalled_blob_names.append(name)

        for name in unmarshalled_blob_names:
            del data.files[name]

        data.data = mutable_data

        return data
