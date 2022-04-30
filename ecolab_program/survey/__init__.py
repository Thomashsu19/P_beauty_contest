from random import choices
from secrets import choice
from otree.api import *


class C(BaseConstants):
    NAME_IN_URL = 'survey'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    gender = models.IntegerField(label="你的性別：",choices=[[0,"男性"],[1,"女性"],[2,"非二元性別"]])
    age = models.IntegerField(label="你的年齡（請填入正整數）：")
    is_eco_or_man_stu = models.BooleanField(label="您是否現在/曾經就讀經濟系或管理學院：",choices=[[1,"是"],[0,"否"]])
    has_studied_eco_class = models.BooleanField(label="您是否修過經濟學相關課程（如：經濟學原理、個體經濟學、總體經濟學等等）",choices=[[1,"是"],[0,"否"]])
    know_pbeauty = models.BooleanField(label="您是否曾經聽過 P-beauty contest game?",choices=[[1,"是"],[0,"否"]])
    guess_goal = models.LongStringField(label="請您簡單描述您覺得本實驗之目的為何？")

# FUNCTIONS
# PAGES
class Survey(Page):
    form_model = 'player'
    form_fields = ["gender", "age", "is_eco_or_man_stu", "has_studied_eco_class", "know_pbeauty", "guess_goal"]

class Finish(Page):
    pass


page_sequence = [Survey, Finish]