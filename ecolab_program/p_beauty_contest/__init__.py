from tokenize import group
from xml.dom.expatbuilder import ElementInfo
from otree.api import *


doc = """
    p_beauty_contest
"""


class C(BaseConstants):
    NAME_IN_URL = 'p_beauty_contest'
    PLAYERS_PER_GROUP = 3 # 實驗組與控制組的人數
    NUM_ROUNDS = 6

    timeout_sec = 30  # 每一回合的決策時間
    timeout_sec_result = 60
    timer_sec = 20  # 出現timer的剩餘時間
    alert_sec = 10  # 出現提醒字樣的剩餘時間

    p = 2/3 
    min_number = 0
    max_number = 100

    winning_prize = 120
    consolation_prize = 10
    
    big_group_player_num = 2 # 大組的人數
    small_group_player_num = 1 # 小組的人數

    noplaying_prize = 10

    ans1 = 30
    ans2 = 10
    ans3 = 60


class Subsession(BaseSubsession):
    treatment_list = models.StringField(initial="")
    

class Group(BaseGroup):
    is_treatment = models.BooleanField()  #實驗組與控制組
    time_pressure = models.BooleanField
    
    num_list_big = models.StringField(initial="所有被選到的號碼有：") # 大組贏家所選的數字
    winner_number_big = models.StringField(initial="本回合贏家的數字是：") # 大組贏家所選的數字
    p_mean_num_big = models.FloatField(initial=-100) # 實驗組或控制組中，大組平均*P值的結果

    num_list_small = models.StringField(initial="所有被選到的號碼有：") # 小組贏家所選的數字
    winner_number_small = models.StringField(initial="本回合贏家的數字是：") # 小組贏家所選的數字
    p_mean_num_small = models.FloatField(initial=-100) # 實驗組或控制組中，小組平均*P值的結果

    num_record_big = models.StringField(initial="") # 本回合大組所選的數字
    num_record_small = models.StringField(initial="") # 本回合小組所選的數字
    num_record_player = models.StringField(initial="") # 本回合所有玩家所選的數字

    mean_num_big = models.FloatField(initial=0) # 實驗組或控制組中，大組的平均
    mean_num_small = models.FloatField(initial=0) # 實驗組或控制組中，小組的平均

    



class Player(BasePlayer):
    is_big_group =  models.BooleanField()
  

    guess_num = models.IntegerField(min=C.min_number, max=C.max_number, label='請輸入您所猜測的非負整數：')
    is_winner = models.BooleanField(initial=False)
    
    decision_duration = models.FloatField(initial=0)  # 決策時間
    is_no_decision = models.BooleanField(initial=False)  # 是否有進行決策
    result_duration = models.FloatField(initial=0)

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
    import random

    if subsession.round_number == 1:
        subsession.group_randomly() # 隨機分組
        player_list = subsession.get_players() # 所有玩家的List

        treatment = [] 
        control = []
        for player in subsession.get_players():
            if player.group.id_in_subsession == 1:
                treatment.append(player) # 如果分到第一組則加入實驗組
            else:
                control.append(player) # 如果分到第二組則加入控制組

        treatment_big = random.sample(treatment, C.big_group_player_num) # 實驗組抽10個，分為大組
        treatment_small = list(set(treatment) - set(treatment_big)) # 實驗組剩3個為小組
        control_big = random.sample(control, C.big_group_player_num) # 控制組抽10個，分為大組
        control_small = list(set(control) - set(control_big)) # 控制組抽3個，分為小組


        for player in subsession.get_players(): 
            if player in treatment:
                player.group.is_treatment = True # 實驗組
                player.participant.is_treatment = True # 存到participant

                if player in treatment_big: # 實驗組_大組
                    player.is_big_group = True
                    player.participant.is_big_group = True
                else:
                    player.is_big_group = False # 實驗組_小組
                    player.participant.is_big_group = False
            else:

                player.group.is_treatment = False # 控制組
                player.participant.is_treatment = False

                if player in control_big: # 控制組大組
                    player.is_big_group = True
                    player.participant.is_big_group = True
                else:
                    player.is_big_group = False # 控制組小組
                    player.participant.is_big_group = False
    

    else:
        subsession.group_like_round(1) # 按第一回合分組
        for player in subsession.get_players(): 
            player.group.is_treatment = player.participant.is_treatment # 按第一回合分配實驗組
            player.is_big_group = player.participant.is_big_group # 按第一回合分配控制組


def set_payoffs(group):
    players_guess_dict_big = {}  # 大組玩家數字的dictionary{players: guess_num}
    players_guess_dict_small = {} # 小組玩家數字的dictionary{players: guess_num}
    total_big = 0 # 大組玩家的總和
    total_small = 0 # 小組玩家的總和
    playing_player_big = 0 # 大組有效玩家數量
    playing_player_small = 0  # 小組有效玩家數量


    # 將所有受試者的數字以 dictionary 形式存下來，將數字加總，並計算有效玩家
    for player in group.get_players():
        if player.is_big_group: 
            if player.is_no_decision == False: 
                players_guess_dict_big[player] = player.guess_num
                total_big += player.guess_num
                playing_player_big += 1

        else:
            if player.is_no_decision == False:
                players_guess_dict_small[player] = player.guess_num
                total_small += player.guess_num
                playing_player_small += 1

    # 有效玩家數字列成表
    counter1 = 0
    for player, num in players_guess_dict_big.items():
        if counter1 < len(players_guess_dict_big):
            group.num_list_big += str(num)+ "、"
            counter1 += 1
        else:
            group.num_list_big += str(num)
        group.num_record_big += str(num) + " " # 紀錄本回合大組玩家數字
        group.num_record_player += str(num) + " " # 紀錄本回合所有玩家數字


    counter2 = 0
    for player, num in players_guess_dict_small.items():
        if counter2 < len(players_guess_dict_small):
            group.num_list_small += str(num)+ "、"
            counter2 += 1
        else:
            group.num_list_small += str(num)

        group.num_record_small += str(num) + " "  # 紀錄本回合小組玩家數字
        group.num_record_player += str(num) + " " # 紀錄本回合所有玩家數字

    



    if playing_player_big > 0:
        mean_big = total_big / playing_player_big
        group.mean_num_big = round(mean_big, 2)
        group.p_mean_num_big = round(mean_big * C.p, 2) # 算出實驗組/對照組中，大組的最終數字
        min_distance_big = 100 # 最小距離
        for player, num in players_guess_dict_big.items():
            if abs(num - group.p_mean_num_big) <= min_distance_big:
                min_distance_big = abs(num - group.p_mean_num_big)
        
        n_winners_big = 0 # 有多少個贏家
        win_num = -100 # 第一個贏家數字
        win2_num = -100 # 第二個贏家數字
        win_num_count = 0 # 幾個贏家數字(0, 1, 2)
        for player, num in players_guess_dict_big.items():
            if abs(num - group.p_mean_num_big) == min_distance_big: # 如果是最小距離則進入條件式
                player.is_winner = True # 玩家為贏家
                n_winners_big += 1 # 贏家數 + 1

                if win_num_count == 0: # 如果還沒統計到贏家數字，則符合條件第一個為win_num
                    win_num = num
                    win_num_count += 1
                
                if win_num_count == 1 and num != win_num: # 已經統計到一個數字，但不是win_num，即為win2_num
                    win2_num = num
                    win_num_count += 1
            
            else:
                player.payoff = C.consolation_prize # 如果不是最小距離則為輸家，給予獎勵
        if win2_num == -100:
            group.winner_number_big += str(win_num)
        else:
            group.winner_number_big += str(win_num) + "、" + str(win2_num)


    if playing_player_small > 0:
        mean_small = total_small / playing_player_small 
        group.mean_num_small = round(mean_small, 2)
        group.p_mean_num_small = round(mean_small * C.p, 2) # 算出實驗組/對照組中，小組的最終數字
        min_distance_small = 100 # 最小距離
        for player, num in players_guess_dict_small.items():
                if abs(num - group.p_mean_num_small) <= min_distance_small:
                    min_distance_small = abs(num - group.p_mean_num_small)
        
        n_winners_small = 0 # 有多少個贏家
        win3_num = -100 # 第一個贏家數字
        win4_num = -100 # 第二個贏家數字
        win_num_count = 0 # 幾個贏家數字(0, 1, 2)
        for player, num in players_guess_dict_small.items():
            if abs(num - group.p_mean_num_small) == min_distance_small: # 如果是最小距離則進入條件式
                player.is_winner = True # 玩家為贏家
                n_winners_small += 1 # 贏家數 + 1

                if win_num_count == 0: # 如果還沒統計到贏家數字，則符合條件第一個為win3_num
                    win3_num = num
                    win_num_count += 1
                
                if win_num_count == 1 and num != win3_num: # 已經統計到一個數字，但不是win3_num，即為win4_num
                    win4_num = num
                    win_num_count += 1
            else:
                player.payoff = C.consolation_prize
        if win4_num == -100:
            group.winner_number_small += str(win3_num)
        else:
            group.winner_number_small += str(win3_num) + "、" + str(win4_num)

    

    for player in group.get_players():
        if player.is_winner:
            if player.is_big_group:
                player.payoff = C.winning_prize / n_winners_big
            elif player.is_big_group == False:
                player.payoff = C.winning_prize / n_winners_small

        if player.is_no_decision == True:
            player.payoff = C.noplaying_prize

    group.num_list_big = group.num_list_big[:-1]
    group.num_list_small = group.num_list_small[:-1]

        


# PAGES
class Instruction(Page):
    @staticmethod
    def is_displayed(player):  # built-in methods
        return player.round_number == 1  # 只有 round 1 要有實驗說明
    @staticmethod
    def vars_for_template(player: Player):  # built-in methods，將 total_payoff 的值傳到 html 頁面
        if player.is_big_group == True:
            player_num = 7
        else:
            player_num = 3
        
        return {
            "num_player_1": player_num - 1
	    }

class Test1(Page):
    form_model = 'player'
    form_fields = ['test1']
    timeout_seconds = 60
    @staticmethod
    def is_displayed(player):  # built-in methods
        return player.round_number == 1  # 只有 round 1 要有實驗說明

class Ans1(Page):
    @staticmethod
    def is_displayed(player):  # built-in methods
        return player.round_number == 1  # 只有 round 1 要有實驗說明
    timeout_seconds = 20
    

class Test2(Page):
    form_model = 'player'
    form_fields = ['test2']
    timeout_seconds = 60
    @staticmethod
    def is_displayed(player):  # built-in methods
        return player.round_number == 1  # 只有 round 1 要有實驗說明

class Ans2(Page):
    @staticmethod
    def is_displayed(player):  # built-in methods
        return player.round_number == 1  # 只有 round 1 要有實驗說明
    timeout_seconds = 20

class Test3(Page):
    form_model = 'player'
    form_fields = ['test3']
    timeout_seconds = 60
    @staticmethod
    def is_displayed(player):  # built-in methods
        return player.round_number == 1  # 只有 round 1 要有實驗說明

class Ans3(Page):
    @staticmethod
    def is_displayed(player):  # built-in methods
        return player.round_number == 1  # 只有 round 1 要有實驗說明
    timeout_seconds = 20

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
    timeout_seconds = C.timeout_sec_result  # built-in
    form_model = "player"
    form_fields = ["result_duration"]


class Finish(Page):
    timeout_seconds = 60

    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS
        
    @staticmethod
    def vars_for_template(player: Player):  # built-in methods，將 total_payoff 的值傳到 html 頁面
        return {
            "total_payoff": sum([p.payoff for p in player.in_all_rounds()])
	    }

page_sequence = [Instruction, Test1, Ans1, Test2, Ans2, Test3, Ans3, DecisionPage, ResultsWaitPage, Results, Finish]
