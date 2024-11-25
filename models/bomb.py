class Bomb:
    def __init__(self, response):
        self.position = (response.get('row'), response.get('col'))
        self.remain_time = response.get('remainTime')
        self.player_id = response.get('playerId')
        self.power = response.get('power')
        self.create_at = response.get('createAt')