class Spoil:
    def __init__(self, response):
        self.position = (response.get('row'), response.get('col'))
        self.spoil_type = response.get('spoilType')