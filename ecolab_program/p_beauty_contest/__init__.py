from pickle import NONE
from re import T
from tokenize import group
from xml.dom.expatbuilder import ElementInfo
from otree.api import *
import random
import time

doc = """
    p_beauty_contest
"""


class C(BaseConstants):
    NAME_IN_URL = 'p_beauty_contest'
    PLAYERS_PER_GROUP = 3
    NUM_ROUNDS = 6
    SHOWUPFEE = 100


    timeout_seconds = 60  # 每一回合的決策時間
    timeout_sec_result = 60
    alert_seconds = 10  # 出現提醒字樣的剩餘時間

    p_twothird = 2/3 
    p_half = 1/2
    min_number = 0
    max_number = 100

    winning_prize = 100
    consolation_prize = 0
    noplaying_prize = 0


    ans1 = 30
    ans1_2 = 22
    ans2 = 10
    ans3 = 60


class Subsession(BaseSubsession):
    first = models.BooleanField(initial=True)

class Group(BaseGroup):
    is_twothird = models.BooleanField(initial=False)  #2/3
    time_pressure = models.BooleanField
    winner_number = models.StringField(initial="本回合贏家的數字是：") # 大組贏家所選的數字
    p_mean_num = models.FloatField(initial=-100) # 平均*P值的結果
    mean_num = models.FloatField(initial=0) # 平均
    player_twothird_num = models.IntegerField(initial=0)
    player_half_num = models.IntegerField(initial=0)
    player_num = models.IntegerField(initial=0)

    



class Player(BasePlayer):
    guess_num = models.IntegerField(min=C.min_number, max=C.max_number, label='請輸入您的決策：')
    is_winner = models.BooleanField(initial=False)
    
    decision_duration = models.FloatField(initial=0)  # 決策時間
    is_no_decision = models.BooleanField(initial=False)  # 是否有進行決策

    test1 = models.IntegerField(label="請填入一個正整數:")
    test2 = models.IntegerField(label="請填入一個正整數:")
    test3 = models.IntegerField(label="請填入一個正整數:")



# FUNCTIONS

def test1_error_message(player, value):
    if player.group.is_twothird:
        if value != C.ans1:
            return '最接近 2/3 倍的平均數的人才是贏家！'
    else:
        if value != C.ans1_2:
            return '最接近 1/2 倍的平均數的人才是贏家！'

def test2_error_message(player, value):
    if value != C.ans2:
        return '每回合的贏家，可獲得報酬 120 元新台幣(超過一位玩家獲勝時，則均分報酬)，其餘玩家可獲得報酬 10 元新台幣。'

def test3_error_message(player, value):
    if value != C.ans3:
        return '每回合的贏家，可獲得報酬 120 元新台幣(超過一位玩家獲勝時，則均分報酬)，其餘玩家可獲得報酬 10 元新台幣。'


# def creating_session(subsession):  
#     if subsession.round_number == 1:
#         player_matrix = []
#         for player in subsession.get_players():
#             player_matrix.append(player)
        
#         random.shuffle(player_matrix)

#         twothird_matrix = []
#         half_matrix = []

#         i = 0
#         for player in player_matrix:
#             if i % 2 == 0:
#                 twothird_matrix.append(player)
#                 i += 1
#             else:
#                 half_matrix.append(player)
#                 i += 1
        
#         matrix = [twothird_matrix, half_matrix]
#         subsession.set_group_matrix(matrix)

#         for player in subsession.get_players():
#             if player.group.id_in_subsession == 1:
#                 player.group.is_twothird = True
        
#     else:
#         subsession.group_like_round(1) # 按第一回合分組
#         for player in subsession.get_players():
#             if player.group.id_in_subsession == 1:
#                 player.group.is_twothird = True
            
def set_payoffs(group):
    if group.id_in_subsession == 2:
        group.is_twothird = True
    players_guess_dict = {}  # 玩家數字的dictionary{players: guess_num}
    total = 0 # 玩家的總和
    playing_player = 0 # 有效玩家數量

    # 將所有受試者的數字以 dictionary 形式存下來，將數字加總，並計算有效玩家
    for player in group.get_players():
        if player.is_no_decision == False: 
            players_guess_dict[player] = player.guess_num
            total += player.guess_num
            playing_player += 1
    
    if playing_player > 0:
        mean = total / playing_player
        group.mean_num = mean
        if group.is_twothird:
            group.p_mean_num = round(mean * C.p_twothird, 2) # 算出實驗組/對照組中，大組的最終數字
        else:
            group.p_mean_num = round(mean * C.p_half, 2) # 算出實驗組/對照組中，大組的最終數字

        min_distance = 100 # 最小距離
        for player, num in players_guess_dict.items():
            if abs(num - group.p_mean_num) <= min_distance:
                min_distance = abs(num - group.p_mean_num)
        
        n_winners = 0 # 有多少個贏家
        win_num = -100 # 第一個贏家數字
        win2_num = -100 # 第二個贏家數字
        win_num_count = 0 # 幾個贏家數字(0, 1, 2)
        winner_matrix = []
        for player, num in players_guess_dict.items():
            if abs(num - group.p_mean_num) == min_distance: # 如果是最小距離則進入條件式
                winner_matrix.append(player)
                n_winners += 1 # 贏家數 + 1

                if win_num_count == 0: # 如果還沒統計到贏家數字，則符合條件第一個為win_num
                    win_num = num
                    win_num_count += 1
                
                if win_num_count == 1 and num != win_num: # 已經統計到一個數字，但不是win_num，即為win2_num
                    win2_num = num
                    win_num_count += 1
            else:
                player.payoff = C.consolation_prize # 如果不是最小距離則為輸家，給予獎勵
        if win2_num == -100:
            group.winner_number += str(win_num)
        else:
            group.winner_number += str(win_num) + "、" + str(win2_num)
    n = 0
    for player in group.get_players():
        player.payoff = C.consolation_prize
        n += 1
        if n == len(group.get_players()):
            if winner_matrix != []:
                winner = random.choice(winner_matrix)
                winner.payoff = C.winning_prize
                winner.is_winner = True

def count_player_num(group):
    for player in group.get_players():
        group.player_num += 1


def waiting_too_long(player):
    participant = player.participant
    return time.time() - participant.wait_page_arrival > 30

def group_by_arrival_time_method(subsession, waiting_players):
    print(waiting_players)
    for player in waiting_players:
        if waiting_too_long(player):
            wait_player_matrix = []
            for waiting_player in waiting_players:
                wait_player_matrix.append(waiting_player)
            random.shuffle(wait_player_matrix)
            n = len(waiting_players)
            if subsession.first == True:
                if n % 2 == 0:
                    n /= 2
                else:
                    n += 1
                    n /= 2
                subsession.first = False
                return wait_player_matrix[:int(n)]
            else:
                return waiting_players



# PAGES


class IntroWaitPage(WaitPage):
    @staticmethod
    def is_displayed(player):  
        return player.round_number == 1  
    after_all_players_arrive = count_player_num
    group_by_arrival_time = True
    title_text = "等待頁面"
    body_text = "請稍待。您至多需要等待五分鐘的時間。"


    

    

class Instruction(Page):
    @staticmethod
    def is_displayed(player):  # built-in methods
        return player.round_number == 1  # 只有 round 1 要有實驗說明
    

class Test1(Page):
    form_model = 'player'
    form_fields = ['test1']
    @staticmethod
    def is_displayed(player):  # built-in methods
        return player.round_number == 1  # 只有 round 1 要有實驗說明

class Ans1(Page):
    @staticmethod
    def is_displayed(player):  # built-in methods
        return player.round_number == 1  # 只有 round 1 要有實驗說明
    

class Test2(Page):
    form_model = 'player'
    form_fields = ['test2']
    @staticmethod
    def is_displayed(player):  # built-in methods
        return player.round_number == 1  # 只有 round 1 要有實驗說明

class Ans2(Page):
    @staticmethod
    def is_displayed(player):  # built-in methods
        return player.round_number == 1  # 只有 round 1 要有實驗說明

class Test3(Page):
    form_model = 'player'
    form_fields = ['test3']
    @staticmethod
    def is_displayed(player):  # built-in methods
        return player.round_number == 1  # 只有 round 1 要有實驗說明

class Ans3(Page):
    @staticmethod
    def is_displayed(player):  # built-in methods
        return player.round_number == 1  # 只有 round 1 要有實驗說明

class DecisionPage(Page):
    form_model = 'player'
    form_fields = ['guess_num', 'decision_duration']
    

class ResultsWaitPage(WaitPage): # built-in
    title_text = "等待頁面"
    body_text = "請稍待。您至多需要等待五分鐘的時間。"
    after_all_players_arrive = set_payoffs  # built-in methods，所有受試者都離開決策頁後，執行 set_payoffs


class Results(Page):
    pass
    

class Finish(Page):

    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS
        
    @staticmethod
    def vars_for_template(player: Player):  # built-in methods，將 total_payoff 的值傳到 html 頁面
        return {
            "total_payoff": round(sum([p.payoff for p in player.in_all_rounds()]) + C.SHOWUPFEE)
	    }

page_sequence = [IntroWaitPage, Instruction, DecisionPage, ResultsWaitPage, Results, Finish]
