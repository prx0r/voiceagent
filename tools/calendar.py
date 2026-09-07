"""Booking adapter boundary. Implement against Google Calendar, Cal.com, ServiceTitan, Jobber, etc."""
async def find_slots(service: str, date: str):
    raise NotImplementedError
