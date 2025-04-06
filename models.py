class DailyAverageRecord:
    def __init__(self, identifier, unit, date):
        self.identifier = identifier
        self.date = date
        self.total = 0.0
        self.unit = unit

    def update(self, value):
        self.total += value

    def __str__(self):
        return f"{self.identifier} measured on {self.date} = {self.total} {self.unit}"

    def to_dict(self):
        return {
            self.date: {
                self.identifier: {
                    "total": self.total,
                    "unit": self.unit
                }
            }
        }


def default_encoder(obj):
    if isinstance(obj, DailyAverageRecord):
        return obj.to_dict()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
