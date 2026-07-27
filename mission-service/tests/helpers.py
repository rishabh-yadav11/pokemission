class MockScalars:
    def __init__(self, data: list):
        self._data = data

    def all(self):
        return self._data

    def first(self):
        return self._data[0] if self._data else None

    def scalar_one_or_none(self):
        return self._data[0] if self._data else None


class MockResult:
    def __init__(self, data):
        self._data = data

    def scalars(self):
        if isinstance(self._data, list):
            return MockScalars(self._data)
        return MockScalars([self._data])

    def scalar_one_or_none(self):
        if isinstance(self._data, list):
            return self._data[0] if self._data else None
        return self._data

    def fetchall(self):
        return self._data if isinstance(self._data, list) else [self._data]

    def all(self):
        if isinstance(self._data, list):
            return self._data
        return [self._data]
