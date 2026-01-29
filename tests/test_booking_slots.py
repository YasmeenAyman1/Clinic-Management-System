import datetime
from repositories.AppointmentRepository import AppointmentRepository


class FakeCursor:
    def __init__(self):
        self.last_query = None
        self._data = []
    def execute(self, query, params=None):
        self.last_query = query.strip().lower()
        # simple behavior: if querying availability, prepare availability rows
        if 'from doctor_availability' in self.last_query:
            # supply a 09:00-11:00 availability
            self._data = [(datetime.time(9,0), datetime.time(11,0))]
        elif 'from appointment' in self.last_query:
            # supply one booked time at 09:30
            self._data = [(datetime.time(9,30),)]
        else:
            self._data = []
    def fetchall(self):
        return self._data
    def fetchone(self):
        return None
    def close(self):
        pass


class FakeConnection:
    def cursor(self):
        return FakeCursor()


def test_get_available_slots_uses_availability():
    repo = AppointmentRepository(connection=FakeConnection())
    slots = repo.get_available_slots(doctor_id=1, date='2025-12-20')
    # Availability 09:00-11:00 with booked 09:30 should give slots 09:00 and 10:00
    assert '09:00' in slots
    assert '09:30' not in slots
    assert '10:00' in slots
    assert '11:00' not in slots


def test_get_available_slots_fallback_when_no_availability():
    class NoAvailCursor(FakeCursor):
        def execute(self, query, params=None):
            self.last_query = query.strip().lower()
            if 'from doctor_availability' in self.last_query:
                self._data = []
            elif 'from appointment' in self.last_query:
                self._data = []
    class NoAvailConn:
        def cursor(self):
            return NoAvailCursor()

    repo = AppointmentRepository(connection=NoAvailConn())
    slots = repo.get_available_slots(doctor_id=1, date='2025-12-20')
    assert '09:00' in slots
    assert '16:30' in slots
    assert '17:00' not in slots
