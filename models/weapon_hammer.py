class WeaponHammer:
    def __init__(self, response):
        self.player_id = response.get('playerId')
        self.power = response.get('power')
        raw_destination = response.get('destination', {})
        self.destination = (raw_destination.get('row'), raw_destination.get('col'))
        self.create_at = response.get('createAt')
