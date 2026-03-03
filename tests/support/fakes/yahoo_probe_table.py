"""Table fakes for Yahoo probe-shape unit tests."""


class FakeRow:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return dict(self._payload)


class FakeILoc:
    def __init__(self, rows):
        self._rows = rows

    def __getitem__(self, index):
        return self._rows[index]


class FakeTable:
    def __init__(self, columns, rows):
        self.columns = columns
        self._rows = [FakeRow(row) for row in rows]
        self.iloc = FakeILoc(self._rows)

    def __len__(self):
        return len(self._rows)
