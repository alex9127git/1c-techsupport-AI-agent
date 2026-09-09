class FileHandler:
    attachments: list[str]

    def __init__(self):
        self.attachments = []

    def is_empty(self):
        return len(self.attachments) == 0

    def add_file(self, file_id: str):
        self.attachments.append(file_id)

    def use(self):
        result = self.attachments[:]
        self.attachments = []
        return result
