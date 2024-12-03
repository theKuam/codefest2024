class WeaponWind:
    def __init__(self, response):
        self.player_id = response.get('playerId')
        self.current_position = (response.get('currentRow'), response.get('currentCol'))
        raw_destination = response.get('destination', {})
        self.direction = response.get('direction')
        self.create_at = response.get('createAt')