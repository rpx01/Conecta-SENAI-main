from datetime import date, datetime, time
from sqlalchemy.inspection import inspect


class SerializerMixin:
    def _serialize_value(self, value):
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, time):
            return value.isoformat(timespec="minutes")
        return value

    def to_dict(self):
        mapper = inspect(self.__class__)
        data = {}
        for column in mapper.columns:
            data[column.key] = self._serialize_value(getattr(self, column.key))
        return data
