from pickle import NONE
from tokenize import group
from xml.dom.expatbuilder import ElementInfo
from otree.api import *


doc = """
    p_beauty_contest
"""


class C(BaseConstants):
    NAME_IN_URL = 'p_beauty_contest'
    PLAYERS_PER_GROUP = 2 # 實驗組與控制組的人數
    NUM_ROUNDS = 6

    timeout_sec = 30  # 每一回合的決策時間
    timeout_sec_result = 60
    timer_sec = 20  # 出現timer的剩餘時間
    alert_sec = 10  # 出現提醒字樣的剩餘時間

    p_twothird = 2/3 
    p_half = 1/2
    min_number = 0
    max_number = 100

    winning_prize = 120
    consolation_prize = 10
    noplaying_prize = 10

    ans1 = 30
    ans2 = 10
    ans3 = 60


class Subsession(BaseSubsession):
    pass
    

class Group(BaseGroup):
    is_twothird = models.BooleanField(initial=False)  #2/3
    time_pressure = models.BooleanField
    winner_number = models.StringField(initial="本回合贏家的數字是：") # 大組贏家所選的數字
    p_mean_num = models.FloatField(initial=-100) # 實驗組或控制組中，大組平均*P值的結果
    mean_num = models.FloatField(initial=0) # 實驗組或控制組中，大組的平均
    player_twothird_num = models.IntegerField(initial=0)
    player_half_num = models.IntegerField(initial=0)

    



class Player(BasePlayer):
    guess_num = models.IntegerField(min=C.min_number, max=C.max_number, label='請輸入您所猜測的非負整數：')
    is_winner = models.BooleanField(initial=False)
    
    decision_duration = models.FloatField(initial=0)  # 決策時間
    is_no_decision = models.BooleanField(initial=False)  # 是否有進行決策

    test1 = models.IntegerField(label="請填入一個正整數:")
    test2 = models.IntegerField(label="請填入一個正整數:")
    test3 = models.IntegerField(label="請填入一個正整數:")

   




# FUNCTIONS

def test1_error_message(player, value):
    print("value is", value)
    if value != C.ans1:
        return '最接近 2/3 倍的平均數的人才是贏家！'

def test2_error_message(player, value):
    print("value is", value)
    if value != C.ans2:
        return '每回合的贏家，可獲得報酬 120 元新台幣(超過一位玩家獲勝時，則均分報酬)，其餘玩家可獲得報酬 10 元新台幣。'

def test3_error_message(player, value):
    print("value is", value)
    if value != C.ans3:
        return '每回合的贏家，可獲得報酬 120 元新台幣(超過一位玩家獲勝時，則均分報酬)，其餘玩家可獲得報酬 10 元新台幣。'



def creating_session(subsession):  # 把組別劃分成實驗組與控制組、大組或小組
    if subsession.round_number == 1:
        subsession.group_randomly() # 隨機分組
        for player in subsession.get_players():
            if player.group.id_in_subsession == 1:
                player.group.is_twothird = True
    else:
        subsession.group_like_round(1) # 按第一回合分組
        for player in subsession.get_players():
            if player.group.id_in_subsession == 1:
                player.group.is_twothird = True



def set_payoffs(group):
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
        for player, num in players_guess_dict.items():
            if abs(num - group.p_mean_num) == min_distance: # 如果是最小距離則進入條件式
                player.is_winner = True # 玩家為贏家
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

    for player in group.get_players():
        if player.is_winner:
            player.payoff = C.winning_prize / n_winners
            
        if player.is_no_decision == True:
            player.payoff = C.noplaying_prize

def count_players(group):
    group.player_twothird_num = round(Subsession.get_players() / 2)
    group.player_half_num = Subsession.get_players() - group.player_twothird_num
        


# PAGES
class Instruction(Page):
    @staticmethod
    def is_displayed(player):  # built-in methods
        return player.round_number == 1  # 只有 round 1 要有實驗說明
    @staticmethod
    def vars_for_template(player: Player):  # built-in methods，將 total_payoff 的值傳到 html 頁面
        if Group.is_twothird:
            player_num = 2
        else:
            player_num = 2
        return {
            "num_player_1": player_num - 1
	    }

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
    timeout_seconds = C.timeout_sec  # built-in

    @staticmethod
    def before_next_page(player, timeout_happened):  # built-in methods
        if timeout_happened:
            player.is_no_decision = True  # 若回合時間到，將 player 設定為沒有做決策

class ResultsWaitPage(WaitPage): # built-in
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
            "total_payoff": sum([p.payoff for p in player.in_all_rounds()])
	    }

page_sequence = [Instruction, Test1, Ans1, Test2, Ans2, Test3, Ans3, DecisionPage, ResultsWaitPage, Results, Finish]
